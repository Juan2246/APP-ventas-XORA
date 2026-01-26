from app import app, db, Variante, Producto, Sale, SaleDetail
import json

def verify_sales_logic():
    client = app.test_client()
    
    with app.app_context():
        # Setup: Ensure we have a Nested Product
        p = Producto.query.filter_by(nombre="Test Cigars Tactile").first()
        if p: db.session.delete(p)
        
        p = Producto(nombre="Test Cigars Tactile", tipo="cigarreria", planchas_por_caja=50, cajetillas_por_plancha=10)
        db.session.add(p)
        db.session.flush()
        
        v = Variante(producto_id=p.id, stock=5000, precio_sugerido=2.0, precio_sugerido_caja=900.0) # 10 Boxes
        db.session.add(v)
        db.session.commit()
        
        var_id = v.id
        print(f"Created Product ID: {var_id}, Stock: 5000 units (10 Boxes)")

    # Test Sale: 1 Box
    print("\n--- Selling 1 Box ---")
    data = {
        "total": 900.0,
        "metodo_pago": "Efectivo",
        "items": [
            {
                "id": f"{var_id}_caja",
                "cantidad": 1,
                "precio": 900.0
            }
        ]
    }
    
    res = client.post("/process_sale", json=data)
    print(f"Sale Status: {res.status_code}")
    
    # Verify Stock
    with app.app_context():
        v = db.session.get(Variante, var_id)
        # Should have deducted 1 Box = 50 * 10 = 500 units.
        # Remaining: 4500.
        print(f"New Stock: {v.stock} (Expected 4500)")
        if v.stock == 4500:
             print("SUCCESS: Stock deduction correct (multiplied by factor).")
        else:
             print("FAILURE: Incorrect stock deduction.")

if __name__ == "__main__":
    verify_sales_logic()
