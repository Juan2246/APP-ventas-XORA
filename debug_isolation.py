from app import app, db, Sale, SaleDetail
from sqlalchemy import func, literal
from datetime import date
import traceback

def test_queries():
    with app.app_context():
        today_str = date.today().strftime('%Y-%m-%d')
        print(f"Today: {today_str} (Type: {type(today_str)})")

        print("\n--- 2. Testing Profit ---")
        try:
            # Use strict literal for 0 if that was the issue?
            # Or just standard
            q = db.session.query(
                func.sum((SaleDetail.precio_unitario - func.coalesce(SaleDetail.costo_unitario, 0)) * SaleDetail.cantidad)
            ).join(Sale).filter(func.date(Sale.fecha) == today_str)
            
            print(f"SQL: {q}")
            val = q.scalar()
            print(f"Profit: {val}")
        except: traceback.print_exc()

if __name__ == "__main__":
    test_queries()
