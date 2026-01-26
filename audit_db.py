from app import app, db, Producto
from sqlalchemy import text

def audit_products():
    with app.app_context():
        # Check for NULL types
        null_products = Producto.query.filter(Producto.tipo == None).all()
        print(f"Products with NULL type: {len(null_products)}")
        for p in null_products:
            print(f"- ID: {p.id}, Name: {p.nombre}")
            
        # Check total products
        total = Producto.query.count()
        print(f"Total Products: {total}")

if __name__ == "__main__":
    audit_products()
