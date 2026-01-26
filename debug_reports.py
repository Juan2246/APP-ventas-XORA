from app import app, db, Sale, SaleDetail, Variante
from sqlalchemy import func
from datetime import date

def debug_data():
    with app.app_context():
        print(f"--- System Date: {date.today()} ---")
        
        # Check Sales
        sales = Sale.query.all()
        print(f"\nTotal Sales found: {len(sales)}")
        for s in sales:
            print(f"ID: {s.id} | Date: {s.fecha} | Total: {s.total}")

        # Check Details (Costs)
        details = SaleDetail.query.all()
        print(f"\nTotal Details found: {len(details)}")
        for d in details[:5]:
            print(f"Detail ID: {d.id} | Price: {d.precio_unitario} | Cost: {d.costo_unitario} | Qty: {d.cantidad}")

        # Check Stock
        low_stock = Variante.query.filter(Variante.stock < 15).count()
        print(f"\nVariants w/ < 15 stock: {low_stock}")

if __name__ == "__main__":
    debug_data()
