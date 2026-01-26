from app import app, db, Sale, SaleDetail, Producto, Variante
from sqlalchemy import func, extract
from datetime import date
import traceback

def test_queries_2():
    with app.app_context():
        print("\n--- 4. Testing Category Profit (Complex Join) ---")
        try:
            # Current implementation in app.py
            q = db.session.query(
                Producto.categoria, 
                func.sum((SaleDetail.precio_unitario - func.coalesce(SaleDetail.costo_unitario, 0)) * SaleDetail.cantidad)
            ).join(Variante).join(SaleDetail).join(Sale).filter(
                extract('year', Sale.fecha) == date.today().year
            ).group_by(Producto.categoria)
            
            print(f"SQL: {q}")
            val = q.all()
            print(f"Cat Profit Rows: {len(val)}")
        except: 
            print("CRASHED!")
            traceback.print_exc()

if __name__ == "__main__":
    test_queries_2()
