from app import app
from database import db
from sqlalchemy import text

def run_migration():
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE productos ADD COLUMN tipo VARCHAR(20) DEFAULT 'general'"))
            print("Added 'tipo' to productos")
        except Exception as e:
            print(f"Skipped 'tipo': {e}")
            
        db.session.commit()
        print("Migration for product types completed.")

if __name__ == "__main__":
    run_migration()
