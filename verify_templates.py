from app import app, db, Variante, Producto
import json

def test_template_system():
    client = app.test_client()
    
    with app.app_context():
        # Cleanup
        for name in ["Test Cutter", "Test Cigars"]:
            p = Producto.query.filter_by(nombre=name).first()
            if p:
                db.session.delete(p)
        db.session.commit()
    
    # 1. Test General Product (Cutter)
    print("\n--- Testing General Product (Cutter) ---")
    data_gen = {
        "nombre": "Test Cutter",
        "categoria": "Accesorios",
        "tipo": "general",
        "stock": 10, # 10 units
        "unit_type": "cajetilla", # Should default to base
        "precio_sugerido": 5.0, # Price per unit
        "precio_costo": 2.0
    }
    client.post("/api/product", json=data_gen)
    
    # Verify
    res = client.get("/api/search?q=Cutter")
    items = res.json
    item = items[0]
    print(f"General Item: {item['nombre']}, Stock: {item['stock']}, Price: {item['precio_sugerido']}")
    if item['stock'] == 10 and item['precio_sugerido'] == 5.0:
        print("SUCCESS: General Product Created correctly.")
    else:
        print("FAILED: General Product data mismatch.")


    # 2. Test Nested Product (Cigars)
    print("\n--- Testing Nested Product (Cigars) ---")
    data_nested = {
        "nombre": "Test Cigars",
        "categoria": "Cigarros",
        "tipo": "cigarreria",
        "planchas_por_caja": 50,
        "cajetillas_por_plancha": 10,
        "stock": 1, 
        "unit_type": "caja",
        "costo_total": 500, # Cost per box -> 1000/500 = 2 per pack? No 500 total cost.
                            # 1 Box = 500 packs. 500 cost / 500 packs = 1 per pack.
        "precio_sugerido_caja": 600,
        "precio_sugerido": 2.0
    }
    client.post("/api/product", json=data_nested)
    
    # Verify
    res = client.get("/api/search?q=Cigars")
    items = res.json
    item = items[0]
    print(f"Nested Item: {item['nombre']}, Stock: {item['stock']}, Cost: {item['precio_costo']}")
    if item['stock'] == 500 and item['precio_costo'] == 1.0:
         print("SUCCESS: Nested Product Created correctly with smart cost calculation.")
    else:
         print(f"FAILED: Nested Product data mismatch. Stock: {item['stock']}, Cost: {item['precio_costo']}")

if __name__ == "__main__":
    test_template_system()
