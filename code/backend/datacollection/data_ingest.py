import os
import requests
from src.database import SessionLocal
from src.models import Object, Image, Tag, Source
from sqlalchemy.exc import IntegrityError
import time

def ingest_data():
    import os
    keywords_path = os.path.join(os.path.dirname(__file__), "keywords")
    try:
        with open(keywords_path, "r") as f:
            queries = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Could not find {keywords_path}, falling back to empty list.")
        queries = []
    base_search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
    base_object_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects"

    object_ids = set()
    print("Searching for artifacts...")
    for q in queries:
        resp = requests.get(base_search_url, params={"hasImages": "true", "q": q})
        if resp.status_code == 200:
            data = resp.json()
            if data.get("objectIDs"):
                # Take up to 50 from each category to provide a massive database without getting DDoSed and IP blocked
                for oid in data["objectIDs"][:50]:
                    object_ids.add(oid)
            time.sleep(0.5)  # Be gentle to the Met API
    
    print(f"Found {len(object_ids)} unique artifacts to ingest.")

    db = SessionLocal()
    from sqlalchemy import text
    try:
        db.execute(text("SELECT setval('sources_id_seq', COALESCE((SELECT MAX(id)+1 FROM sources), 1), false)"))
        db.execute(text("SELECT setval('objects_id_seq', COALESCE((SELECT MAX(id)+1 FROM objects), 1), false)"))
        db.execute(text("SELECT setval('images_id_seq', COALESCE((SELECT MAX(id)+1 FROM images), 1), false)"))
        db.execute(text("SELECT setval('tags_id_seq', COALESCE((SELECT MAX(id)+1 FROM tags), 1), false)"))
        db.commit()
    except Exception as e:
        print("Could not update sequences:", e)
        db.rollback()
    
    # Removed generic source creation

    count = 0
    for oid in list(object_ids):
        # Throttle request to avoid rate limit and Cloudflare ban
        time.sleep(1)
        resp = requests.get(f"{base_object_url}/{oid}")
        if resp.status_code != 200:
            continue
            
        obj_data = resp.json()
        
        # We need essentially some minimal data.
        inventory_num = obj_data.get("accessionNumber")
        if not inventory_num:
            continue
            
        artist = obj_data.get("artistDisplayName", "")
        if artist:
            artist = f"{artist}. "
        title = obj_data.get("title") or obj_data.get("objectName") or "Unknown Title"
        date = obj_data.get("objectDate", "Unknown Date")
        medium = obj_data.get("medium", "Unknown medium")
        repo = obj_data.get("repository", "The Metropolitan Museum of Art")
        url = obj_data.get("objectURL", "")
        
        biblio = f"{artist}{title}. {date}. {medium}. {repo}. {url}".strip()
        
        import re
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            import subprocess, sys
            print("Installing BeautifulSoup4...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
            from bs4 import BeautifulSoup

        desc_text = ""
        object_url = obj_data.get("objectURL")
        if object_url:
            try:
                page_resp = requests.get(object_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                if page_resp.status_code == 200:
                    bs = BeautifulSoup(page_resp.text, 'html.parser')
                    divs = bs.find_all(attrs={'data-testid': 'read-more-content'})
                    if divs:
                        desc_text = divs[0].get_text(separator=' ', strip=True)
                    else:
                        match = re.search(r'<meta\s+(?:property|name)=[\'"]og:description[\'"]\s+content=[\'"](.*?)[\'"]\s*/?>', page_resp.text, re.IGNORECASE)
                        if match:
                            desc_text = match.group(1).replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
            except Exception as e:
                print(f"Could not fetch description from {object_url}: {e}")
        
        if not desc_text:
            desc_text = f"An artifact characterized by its {obj_data.get('medium', 'materials')} from the {obj_data.get('culture', 'unknown')} culture, dating to {obj_data.get('objectDate', 'an unknown period')}."
        
        # Get or create source
        source = db.query(Source).filter_by(citation_text=biblio).first()
        if not source:
            source = Source(citation_text=biblio)
            db.add(source)
            db.commit()
            db.refresh(source)
            
        # Check if already exists
        existing_obj = db.query(Object).filter_by(inventory_number=inventory_num).first()
        if existing_obj:
            print(f"Object {inventory_num} already exists, updating bibliography and description.")
            for img in existing_obj.images:
                img.source_id = source.id
            existing_obj.description = desc_text
            db.commit()
            continue
            
        # Ensure we have a primary image
        primary_image = obj_data.get("primaryImage")
        if not primary_image:
            continue

        obj = Object(
            object_type=obj_data.get("objectName") or obj_data.get("title") or "Unknown Artifact",
            material=obj_data.get("medium") or "Unknown",
            findspot=obj_data.get("region") or obj_data.get("locale") or obj_data.get("country") or "Unknown",
            inventory_number=inventory_num,
            description=desc_text,
            date_display=obj_data.get("objectDate") or "Unknown",
            date_start=obj_data.get("objectBeginDate") or 0,
            date_end=obj_data.get("objectEndDate") or 0
        )
        
        db.add(obj)
        try:
            db.commit()
            db.refresh(obj)
        except IntegrityError:
            db.rollback()
            continue

        # Add image
        img = Image(
            object_id=obj.id,
            source_id=source.id,
            image_type="Primary",
            view_type="Front",
            file_url=primary_image
        )
        db.add(img)
        
        # Process Tags
        tags_data = obj_data.get("tags")
        if tags_data:
            for tag_info in tags_data:
                tag_name = tag_info.get("term")
                if not tag_name: continue
                tag = db.query(Tag).filter_by(tag_name=tag_name).first()
                if not tag:
                    tag = Tag(tag_name=tag_name)
                    db.add(tag)
                    db.commit()
                    db.refresh(tag)
                img.tags.append(tag)
                
        # Handle additional images if any
        add_images = obj_data.get("additionalImages", [])
        for add_url in add_images[:3]:  # Limit to 3 additional images to save space
            add_img = Image(
                object_id=obj.id,
                source_id=source.id,
                image_type="Additional",
                view_type="Unknown",
                file_url=add_url
            )
            # Maybe apply the same tags to additional images
            if tags_data:
                for tag_info in tags_data:
                    tag_name = tag_info.get("term")
                    if tag_name:
                        t = db.query(Tag).filter_by(tag_name=tag_name).first()
                        if t: add_img.tags.append(t)
            db.add(add_img)

        try:
            db.commit()
            count += 1
            print(f"Successfully added obj {inventory_num} ({count})")
        except Exception as e:
            db.rollback()
            print(f"Failed to add images for {inventory_num}: {e}")

    print(f"Ingestion complete. Added {count} artifacts.")
    db.close()

if __name__ == "__main__":
    ingest_data()
