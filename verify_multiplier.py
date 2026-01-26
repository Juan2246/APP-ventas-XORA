import urllib.request
import json
import time
import subprocess
import sys

BASE_URL = 'http://127.0.0.1:5000'

def request_json(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    if data:
        body = json.dumps(data).encode('utf-8')
        req.data = body
    
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Request failed: {method} {endpoint} - {e}")
        return None

def test_multiplier_logic():
    print("--- Testing Multiplier Logic ---")
    
    # 1. Create Base Product (Pack)
    print("Creating Base Product (Pack)...")
    res1 = request_json('POST', '/api/product', {
        'nombre': 'TestCigarros',
        'categoria': 'Cigarros',
        'origen': 'TestOrigin',
        'diseno': 'TestDesign',
        'stock': 100, # 100 units
        'precio_costo': 5,
        'precio_sugerido': 10,
        'multiplicador': 1
    })
    print(res1)
    
    # Get ID of created variant
    inv = request_json('GET', '/api/inventory')
    base_variant = next((v for v in inv if v['producto'] == 'TestCigarros' and v['multiplicador'] == 1), None)
    if not base_variant:
        print("FAIL: Base variant not found")
        return
    print(f"Base Variant ID: {base_variant['id']} | Stock: {base_variant['stock']}")

    # 2. Create Presentation (Box) - Multiplier 10
    print("Creating Presentation (Box)...")
    res2 = request_json('POST', '/api/product', {
        'nombre': 'TestCigarros', # Same name
        'origen': 'TestOrigin',   # Same origin
        'diseno': 'TestDesign',   # Same design
        'stock': 0,               # Don't add extra stock, just link
        'precio_costo': 50,
        'precio_sugerido': 90,
        'multiplicador': 10,
        'fecha_vencimiento': ''
    })
    print(res2)
    
    inv = request_json('GET', '/api/inventory')
    box_variant = next((v for v in inv if v['producto'] == 'TestCigarros' and v['multiplicador'] == 10), None)
    if not box_variant:
        print("FAIL: Box variant not found")
        return
    
    print(f"Box Variant ID: {box_variant['id']} | Stock Visual: {box_variant['stock']} | Real: {box_variant['stock_real']}")
    
    # Check Sync - If Base has 100, Box (Mul 10) should have Visual 10
    if box_variant['stock'] == 10 and box_variant['stock_real'] == 100:
        print("PASS: Stock Initial Sync (100 units = 10 boxes)")
    else:
        print(f"FAIL: Stock Sync Mismatch. Expected 10/100, got {box_variant['stock']}/{box_variant['stock_real']}")

    # 3. Process Sale - Sell 1 Box
    print("Selling 1 Box...")
    sale_res = request_json('POST', '/process_sale', {
        'total': 90,
        'metodo_pago': 'Efectivo',
        'items': [{
            'id': box_variant['id'],
            'cantidad': 1,
            'precio': 90
        }]
    })
    print(sale_res)

    # 4. Verify Deduction
    # Should deduct 1 * 10 = 10 units. Remaining: 90 units.
    # Base Variant: 90 units.
    # Box Variant: 9 units.
    
    inv = request_json('GET', '/api/inventory')
    base_check = next(v for v in inv if v['id'] == base_variant['id'])
    box_check = next(v for v in inv if v['id'] == box_variant['id'])
    
    print(f"After Sale - Base Stock: {base_check['stock']} (Exp 90)")
    print(f"After Sale - Box Stock: {box_check['stock']} (Exp 9)")
    
    if base_check['stock'] == 90 and box_check['stock'] == 9:
        print("PASS: Sale Deduction Logic Correct.")
    else:
        print("FAIL: Sale Deduction Failed.")

if __name__ == "__main__":
    # Start app
    p = subprocess.Popen([sys.executable, 'app.py'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    time.sleep(3)
    try:
        test_multiplier_logic()
    finally:
        p.terminate()
