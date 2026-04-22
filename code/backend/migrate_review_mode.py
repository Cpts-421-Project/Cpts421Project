import os
import sys
from sqlalchemy import create_engine, text

# Add src to python path for imports to work
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.database import get_engine

def migrate_review_status():
    print("Starting migration: Adding review_status to objects table...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='objects' AND column_name='review_status'"))
            if result.fetchone():
                print("Column 'review_status' already exists. Skipping.")
                return

            # Add column
            conn.execute(text("ALTER TABLE objects ADD COLUMN review_status VARCHAR(50) DEFAULT 'pending'"))
            
            # Set all existing artifacts to 'accepted' so they don't disappear from users
            conn.execute(text("UPDATE objects SET review_status = 'accepted'"))
            
            # Create index for fetching pending queues efficiently
            conn.execute(text("CREATE INDEX ix_objects_review_status ON objects (review_status)"))
            
            conn.commit()
            print("Migration successful! Existing objects marked as 'accepted'.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_review_status()
