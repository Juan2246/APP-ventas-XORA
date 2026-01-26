from app import app
import json

def verify_inventory_load():
    client = app.test_client()
    
    print("Testing /api/search?q=")
    res = client.get('/api/search?q=')
    data = res.json
    
    print(f"Status: {res.status_code}")
    print(f"Items found: {len(data)}")
    
    if len(data) > 0:
        print("SUCCESS: Items returned.")
        print("First item:", data[0]['nombre'])
    else:
        print("FAILURE: No items returned (unexpected if db has items).")

if __name__ == "__main__":
    verify_inventory_load()
