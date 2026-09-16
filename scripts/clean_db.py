from app import app, db, Categoria, Origen

def clean_database():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        
        print("Seeding default data...")
        defaults_cat = ['Ropa', 'Accesorios', 'Juguetes', 'Cigarros', 'Otros']
        for name in defaults_cat:
            db.session.add(Categoria(nombre=name))
            
        defaults_orig = ['China', 'Perú']
        for name in defaults_orig:
            db.session.add(Origen(nombre=name))
            
        db.session.commit()
        print("Database cleaned and initialized successfully.")

if __name__ == "__main__":
    clean_database()
