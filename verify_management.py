from app import app, db, Producto, Categoria, Origen

def verify_management():
    client = app.test_client()
    
    with app.app_context():
        # 1. Add Test Category
        print("--- Adding Test Category ---")
        client.post('/api/category', json={'nombre': 'TestCategory'})
        if Categoria.query.filter_by(nombre='TestCategory').first():
            print("SUCCESS: Category created.")
        else:
            print("FAILURE: Category not created.")
            return

        # 2. Add Product using it
        print("\n--- Assigning to Product ---")
        p = Producto.query.first()
        if not p:
            p = Producto(nombre="TempProd")
            db.session.add(p)
        
        old_cat = p.categoria
        p.categoria = 'TestCategory'
        db.session.commit()
        
        # 3. Try to Delete (Should Fail)
        print("\n--- Try Delete (Should Fail) ---")
        res = client.delete('/api/category/TestCategory')
        print(f"Status: {res.status_code}, Msg: {res.json.get('message')}")
        if res.status_code == 400:
            print("SUCCESS: Deletion blocked.")
        else:
            print("FAILURE: Deletion was allowed unexpectedly.")

        # 4. Remove usage
        print("\n--- Remove Usage ---")
        p.categoria = old_cat
        db.session.commit()
        
        # 5. Try Delete (Should Succeed)
        print("\n--- Try Delete (Should Succeed) ---")
        res = client.delete('/api/category/TestCategory')
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
             if not Categoria.query.filter_by(nombre='TestCategory').first():
                 print("SUCCESS: Category deleted.")
             else:
                 print("FAILURE: Category still exists.")
        else:
            print("FAILURE: Deletion failed.")

if __name__ == "__main__":
    verify_management()
