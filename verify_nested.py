from app import app, db, Variante, Producto
import json

def test_flow():
    client = app.test_client()
    
    with app.app_context():
        # Cleanup previous test data
        p = Producto.query.filter_by(nombre="Test Marlboro").first()
        if p:
            db.session.delete(p)
            db.session.commit()
            print("Cleaned up previous test data.")

    print("\n--- Testing Product Creation (Nested) ---")
    data = {
        "nombre": "Test Marlboro",
        "categoria": "Cigarros",
        "origen": "USA",
        "diseno": "Red",
        "planchas_por_caja": 5, 
        "cajetillas_por_plancha": 10,
        "stock": 1, 
        "unit_type": "caja",
        "costo_total": 500,
        "precio_sugerido_caja": 600,
        "precio_sugerido_plancha": 120,
        "precio_sugerido": 15
    }
    
    res = client.post("/api/product", json=data)
    print(f"Create Status: {res.status_code}")
    print(f"Create Response: {res.json}")

    print("\n--- Testing Search (Should return 3 options) ---")
    res = client.get("/api/search_variants?q=Marlboro")
    items = res.json
    print(f"Found {len(items)} items")
    
    sheet_item = None
    for item in items:
        print(f"- {item['nombre_completo']}: Price S/{item['precio_sugerido']}, Stock {item['stock']}, ID {item['id']}")
        if 'PLANCHA' in item['nombre_completo']:
            sheet_item = item

    if not sheet_item:
        print("FAILED: No Sheet item found")
        return

    print("\n--- Testing Sale (Selling 1 Sheet) ---")
    data = {
        "total": sheet_item['precio_sugerido'],
        "metodo_pago": "Efectivo",
        "items": [
            {
                "id": sheet_item['id'],
                "cantidad": 1,
                "precio": sheet_item['precio_sugerido']
            }
        ]
    }
    
    res = client.post("/process_sale", json=data)
    print(f"Sale Status: {res.status_code}")
    print(f"Sale Response: {res.json}")

    print("\n--- Verifying Stock After Sale ---")
    # We sold 1 Sheet (10 packs). Initial 1 Box (50 packs). Remaining 40 packs.
    res = client.get("/api/search_variants?q=Marlboro")
    items = res.json
    base_item = next((i for i in items if 'CAJETILLA' in i['nombre_completo']), None)
    if base_item:
        print(f"Base Stock: {base_item['stock']} (Expected 40)")
        if base_item['stock'] == 40:
            print("SUCCESS: Stock verification passed.")
        else:
            print("FAILED: Stock verification failed.")

if __name__ == "__main__":
    test_flow()
