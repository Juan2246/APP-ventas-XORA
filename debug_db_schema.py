import sqlite3
import os

DB_PATH = 'marketflow.db'

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check 'variantes' table info
    print("--- Table: variantes ---")
    cursor.execute("PRAGMA table_info(variantes)")
    columns = [row[1] for row in cursor.fetchall()]
    print(columns)
    
    if 'precio_costo' in columns:
        print("PASS: 'precio_costo' exists in 'variantes'.")
    else:
        print("FAIL: 'precio_costo' MISSING in 'variantes'.")

    # Check 'sale_details' table info
    print("\n--- Table: sale_details ---")
    cursor.execute("PRAGMA table_info(sale_details)")
    columns = [row[1] for row in cursor.fetchall()]
    print(columns)

    if 'costo_unitario' in columns:
        print("PASS: 'costo_unitario' exists in 'sale_details'.")
    else:
        print("FAIL: 'costo_unitario' MISSING in 'sale_details'.")

    conn.close()

if __name__ == "__main__":
    check_db()
