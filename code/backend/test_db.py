import sys
sys.path.append("src")
from src.database import get_engine
from sqlalchemy.orm import Session
from src.services.object_service import ObjectService

engine = get_engine()
with Session(engine) as session:
    service = ObjectService(session)
    res = service.get_pending_objects()
    print(f"Service returned {len(res)} objects.")
    if len(res) > 0:
        print(f"First object keys: {res[0].keys()}")
        print(f"First object images: {res[0].get('images')}")
