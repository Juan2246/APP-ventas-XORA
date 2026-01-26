from database import db
from app import app
from sqlalchemy import text

def run_migration():
    with app.app_context():
        # Add columns to productos
        try:
            db.session.execute(text("ALTER TABLE productos ADD COLUMN planchas_por_caja INTEGER DEFAULT 1"))
            print("Added planchas_por_caja to productos")
        except Exception as e:
            print(f"Skipped planchas_por_caja: {e}")

        try:
            db.session.execute(text("ALTER TABLE productos ADD COLUMN cajetillas_por_plancha INTEGER DEFAULT 1"))
            print("Added cajetillas_por_plancha to productos")
        except Exception as e:
            print(f"Skipped cajetillas_por_plancha: {e}")

        # Add columns to variantes
        try:
            db.session.execute(text("ALTER TABLE variantes ADD COLUMN precio_sugerido_plancha FLOAT DEFAULT 0.0"))
            print("Added precio_sugerido_plancha to variantes")
        except Exception as e:
            print(f"Skipped precio_sugerido_plancha: {e}")

        try:
            db.session.execute(text("ALTER TABLE variantes ADD COLUMN precio_sugerido_caja FLOAT DEFAULT 0.0"))
            print("Added precio_sugerido_caja to variantes")
        except Exception as e:
            print(f"Skipped precio_sugerido_caja: {e}")

        db.session.commit()
        print("Migration completed.")

if __name__ == "__main__":
    run_migration()
