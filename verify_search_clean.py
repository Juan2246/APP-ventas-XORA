from app import app, db, Variante, Producto
import json

def debug_clean_search():
    client = app.test_client()
    print("\n--- Searching for 'Cut' (General) ---")
    res = client.get('/api/search_variants?q=Cut')
    data = res.json
    for item in data:
        print(f"ID: {item['id']}, Name: {item['nombre_completo']}, Price: {item['precio_sugerido']}")
        
    print("\n--- Searching for 'Cigar' (Nested) ---")
    res = client.get('/api/search_variants?q=Cigar')
    data = res.json
    for item in data:
        print(f"ID: {item['id']}, Name: {item['nombre_completo']}, Price: {item['precio_sugerido']}")

if __name__ == "__main__":
    debug_clean_search()
