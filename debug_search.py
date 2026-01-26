from app import app, db, Variante, Producto
import json

def debug_search_variants():
    client = app.test_client()
    
    # 1. Ensure we have a General product
    with app.app_context():
        p = Producto.query.filter(Producto.nombre.ilike('%Cutter%')).first()
        if not p:
            print("Creating Test Cutter for debugging...")
            p = Producto(nombre="Test Cutter", tipo="general", planchas_por_caja=1, cajetillas_por_plancha=1)
            db.session.add(p)
            db.session.flush()
            v = Variante(producto_id=p.id, stock=100, precio_sugerido=5.0)
            db.session.add(v)
            db.session.commit()
            print("Test Cutter created.")
        else:
             print(f"Found existing Cutter: {p.nombre}")

    # 2. Search for it
    print("\n--- Searching for 'Cut' ---")
    res = client.get('/api/search_variants?q=Cut')
    data = res.json
    
    print(f"Status: {res.status_code}")
    print(f"Items found: {len(data)}")
    for item in data:
        print(f"ID: {item['id']}, Name: {item['nombre_completo']}, Price: {item['precio_sugerido']}")

if __name__ == "__main__":
    debug_search_variants()
