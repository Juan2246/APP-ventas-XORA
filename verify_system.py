import sqlite3
import os
import urllib.request
import urllib.error
import time
import subprocess
import sys

# Config
DB_PATH = os.path.join('instance', 'marketflow.db')
BASE_URL = 'http://127.0.0.1:5000'

def check_db_schema():
    print(f"--- Database Verification ({DB_PATH}) ---")
    if not os.path.exists(DB_PATH):
        print(f"FAIL: Database file not found at {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    issues_found = False

    # Check 'variantes' columns
    try:
        cursor.execute("PRAGMA table_info(variantes)")
        cols_variantes = {row[1] for row in cursor.fetchall()}
        print(f"DEBUG: variantes columns = {cols_variantes}")
        
        if 'precio_costo' not in cols_variantes:
            print("FAIL: Column 'precio_costo' missing in 'variantes'")
            issues_found = True
        else:
            print("PASS: 'precio_costo' exists in 'variantes'")

        # Check 'sale_details' columns
        cursor.execute("PRAGMA table_info(sale_details)")
        cols_details = {row[1] for row in cursor.fetchall()}
        print(f"DEBUG: sale_details columns = {cols_details}")

        if 'costo_unitario' not in cols_details:
            print("FAIL: Column 'costo_unitario' missing in 'sale_details'")
            issues_found = True
        else:
            print("PASS: 'costo_unitario' exists in 'sale_details'")
            
    except Exception as e:
        print(f"FAIL: Database check error: {e}")
        issues_found = True

    conn.close()
    return not issues_found

def test_endpoints():
    print("\n--- Endpoint Verification ---")
    # Wait for server to start
    time.sleep(5)
    
    endpoints = [
        '/',
        '/inventario',
        '/api/search_variants?q=test',
        '/api/inventory',
        '/billing',
    ]

    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    print(f"PASS: GET {endpoint} returned 200")
                else:
                    print(f"FAIL: GET {endpoint} returned {response.status}")
        except urllib.error.HTTPError as e:
            print(f"FAIL: GET {endpoint} returned {e.code}")
        except urllib.error.URLError as e:
            print(f"FAIL: GET {endpoint} request failed: {e.reason}")
        except Exception as e:
            print(f"FAIL: GET {endpoint} unexpected error: {e}")

if __name__ == "__main__":
    # 1. Check DB first
    db_ok = check_db_schema()
    
    # 2. Start App in background to test routes
    print("\n--- Starting App for Route Testing ---")
    process = subprocess.Popen([sys.executable, 'app.py'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    
    try:
        # Give it a moment to possibly fail
        time.sleep(2)
        if process.poll() is not None:
             # Process died
             _, errs = process.communicate()
             print(f"CRITICAL: App failed to start.\nErrors:\n{errs}")
        else:
            test_endpoints()
    finally:
        process.terminate()
        print("\n--- Verification Complete ---")
