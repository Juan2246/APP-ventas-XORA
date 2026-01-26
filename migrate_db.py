import sqlite3
import os

DB_PATH = os.path.join('instance', 'marketflow.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Add precio_costo to variantes
    try:
        cursor.execute("PRAGMA table_info(variantes)")
        cols = {row[1] for row in cursor.fetchall()}
        if 'precio_costo' not in cols:
            print("Adding precio_costo to variantes...")
            cursor.execute("ALTER TABLE variantes ADD COLUMN precio_costo FLOAT DEFAULT 0.0")
        else:
             print("precio_costo already in variantes.")
    except Exception as e:
        print(f"Error migrating variantes: {e}")

    # 2. Add costo_unitario to sale_details
    try:
        cursor.execute("PRAGMA table_info(sale_details)")
        cols = {row[1] for row in cursor.fetchall()}
        if 'costo_unitario' not in cols:
            print("Adding costo_unitario to sale_details...")
            cursor.execute("ALTER TABLE sale_details ADD COLUMN costo_unitario FLOAT DEFAULT 0.0")
        else:
             print("costo_unitario already in sale_details.")
    except Exception as e:
        print(f"Error migrating sale_details: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
