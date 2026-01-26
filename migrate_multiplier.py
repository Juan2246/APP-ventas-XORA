import sqlite3
import os

DB_PATH = os.path.join('instance', 'marketflow.db')

def migrate_multiplicador():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(variantes)")
        cols = {row[1] for row in cursor.fetchall()}
        
        if 'multiplicador' not in cols:
            print("Adding 'multiplicador' to variantes...")
            cursor.execute("ALTER TABLE variantes ADD COLUMN multiplicador FLOAT DEFAULT 1.0")
        else:
             print("'multiplicador' already exists.")
             
    except Exception as e:
        print(f"Error migrating: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_multiplicador()
