from flask import Flask, render_template, request, jsonify
from database import db, init_db, Producto, Variante, Sale, SaleDetail, Categoria, Origen
from sqlalchemy import func, extract
from datetime import datetime, timedelta, date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    return render_template('billing.html')

@app.route('/billing')
def billing():
    return render_template('billing.html')

@app.route('/inventario')
def inventory():
    return render_template('inventory.html')

# --- API Endpoints ---

@app.route('/api/search_variants', methods=['GET'])
def search_variants_api():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = db.session.query(Variante, Producto).join(Producto).filter(
        (Producto.nombre.ilike(f'%{query}%')) | 
        (Variante.origen.ilike(f'%{query}%')) |
        (Variante.diseno.ilike(f'%{query}%')) 
    ).all()

    data = []
    for variante, producto in results:
        # Construct simplified base name
        attributes = [attr for attr in [variante.origen, variante.diseno] if attr]
        attr_str = f" ({' - '.join(attributes)})" if attributes else ""
        base_name = f"{producto.nombre}{attr_str}"
        
        # General Products: Single simplified entry
        if producto.tipo == 'general':
            data.append({
                'id': variante.id, # Send raw ID
                'nombre_completo': base_name,
                'precio_sugerido': variante.precio_sugerido,
                'stock': int(variante.stock),
                'multiplicador': 1
            })
            continue

        # Cigarrería (Nested) Products: 3 Options
        
        # Multipliers
        pack_per_sheet = producto.cajetillas_por_plancha or 1
        sheet_per_box = producto.planchas_por_caja or 1
        pack_per_box = pack_per_sheet * sheet_per_box
        
        # 1. Caja
        if variante.precio_sugerido_caja > 0:
            data.append({
                'id': f"{variante.id}_caja",
                'nombre_completo': f"{base_name} - CAJA x{sheet_per_box} Planchas",
                'precio_sugerido': variante.precio_sugerido_caja,
                'stock': int(variante.stock // pack_per_box),
                'multiplicador': pack_per_box
            })
            
        # 2. Plancha
        if variante.precio_sugerido_plancha > 0:
             data.append({
                'id': f"{variante.id}_plancha",
                'nombre_completo': f"{base_name} - PLANCHA x{pack_per_sheet} Cajetillas",
                'precio_sugerido': variante.precio_sugerido_plancha,
                'stock': int(variante.stock // pack_per_sheet),
                'multiplicador': pack_per_sheet
            })
            
        # 3. Cajetilla (Base) - Always show
        data.append({
            'id': f"{variante.id}_cajetilla",
            'nombre_completo': f"{base_name} - CAJETILLA",
            'precio_sugerido': variante.precio_sugerido,
            'stock': int(variante.stock),
            'multiplicador': 1
        })

    return jsonify(data)

@app.route('/api/search', methods=['GET'])
def search_products():
    query = request.args.get('q', '')
    
    # If query is empty, return all (LIMIT 50 or 100 to be safe? Or just all)
    # User inventory usually needs all to see stats.
    if not query:
        results = db.session.query(Variante, Producto).join(Producto).all()
    else:
        results = db.session.query(Variante, Producto).join(Producto).filter(
            (Producto.nombre.ilike(f'%{query}%')) | 
            (Variante.origen.ilike(f'%{query}%')) |
            (Variante.diseno.ilike(f'%{query}%')) 
        ).all()

    data = []
    for variante, producto in results:
        data.append({
            'id': variante.id,
            'nombre': producto.nombre,
            'categoria': producto.categoria,
            'origen': variante.origen,
            'diseno': variante.diseno, 
            'precio_sugerido': variante.precio_sugerido,
            'stock': variante.stock,
            # Add config for FE Edit
            'planchas_por_caja': producto.planchas_por_caja,
            'cajetillas_por_plancha': producto.cajetillas_por_plancha,
            'precio_sugerido_plancha': variante.precio_sugerido_plancha,
            'precio_sugerido_caja': variante.precio_sugerido_caja,
            'precio_costo': variante.precio_costo
        })
    return jsonify(data)

@app.route('/process_sale', methods=['POST'])
def process_sale():
    data = request.json
    try:
        new_sale = Sale(
            total=data['total'],
            metodo_pago=data['metodo_pago']
        )
        db.session.add(new_sale)
        db.session.flush()

        for item in data['items']:
            # Item ID comes as "123_caja" or just "123" (legacy/pure id)
            raw_id = str(item['id'])
            if '_' in raw_id:
                parts = raw_id.split('_')
                var_id = int(parts[0])
                unit_type = parts[1]
            else:
                var_id = int(raw_id)
                unit_type = 'cajetilla'

            variante = db.session.get(Variante, var_id)
            if not variante:
                 raise Exception(f"Variante {raw_id} no encontrada")
            
            # Determine logic multiplier
            producto = variante.producto
            multiplier = 1
            if unit_type == 'caja':
                multiplier = (producto.planchas_por_caja or 1) * (producto.cajetillas_por_plancha or 1)
            elif unit_type == 'plancha':
                multiplier = (producto.cajetillas_por_plancha or 1)
            
            deduction_units = item['cantidad'] * multiplier
            
            if variante.stock < deduction_units:
                 current_stock_display = int(variante.stock // multiplier)
                 raise Exception(f"Stock insuficiente para {producto.nombre} ({unit_type}). Disponible: {current_stock_display}")

            # Update Stock
            # (If we assume only 1 Variant row per product/origin/design, we just update it. 
            # If there are siblings (duplicates?), we sync them.)
            siblings = db.session.query(Variante).filter_by(
                producto_id=variante.producto_id, 
                origen=variante.origen, 
                diseno=variante.diseno
            ).all()
            
            new_stock_level = variante.stock - deduction_units
            
            for sib in siblings:
                sib.stock = new_stock_level
            
            detail = SaleDetail(
                sale_id=new_sale.id,
                variante_id=variante.id,
                cantidad=item['cantidad'], # Quantity of BOXES/SHEETS
                precio_unitario=item['precio'], # Price per BOX/SHEET
                costo_unitario=variante.precio_costo * multiplier # Cost per BOX/SHEET
            )
            # Annotate detail with unit type? Schema doesn't have it, but we can store it in custom field if needed.
            # Use 'diseno' hack or just assume price reflects it?
            # User wants to know profit. profit = (price - cost). Cost is scaled correctly above.
            
            db.session.add(detail)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Venta procesada correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/product', methods=['POST'])
def manage_product():
    data = request.json
    try:
        variant_id = data.get('variant_id')
        action_type = data.get('action_type', 'new') # new, restock, edit

        if variant_id:
            variante = Variante.query.get(variant_id)
            if not variante:
                 return jsonify({'success': False, 'message': 'Variante no encontrada'}), 404
            
            producto = variante.producto

            if action_type == 'edit':
                # Edit Existing
                producto.nombre = data['nombre']
                producto.categoria = data.get('categoria')
                producto.tipo = data.get('tipo', 'general')

                # Config params (Reset to 1 if general for safety, or keep? Better to allow reset)
                if producto.tipo == 'general':
                    producto.planchas_por_caja = 1
                    producto.cajetillas_por_plancha = 1
                else:
                    producto.planchas_por_caja = int(data.get('planchas_por_caja', 1))
                    producto.cajetillas_por_plancha = int(data.get('cajetillas_por_plancha', 1))
                
                variante.origen = data.get('origen')
                variante.diseno = data.get('diseno')
                
                # Prices
                variante.precio_sugerido = float(data.get('precio_sugerido', 0))
                
                if producto.tipo == 'cigarreria':
                     variante.precio_sugerido_plancha = float(data.get('precio_sugerido_plancha', 0))
                     variante.precio_sugerido_caja = float(data.get('precio_sugerido_caja', 0))
                else:
                     variante.precio_sugerido_plancha = 0
                     variante.precio_sugerido_caja = 0

                variante.precio_costo = float(data.get('precio_costo', 0))

                # Stock update handled via restock usually, skipped here for edit except for simple property update?
                # User asked for "Stock Normalization". 
                # If we are editing, we usually don't touch stock unless specific "Adjustment" flow. 

            elif action_type == 'restock':
                # Restock
                qty = int(data.get('stock', 0))
                unit_type = data.get('unit_type', 'cajetilla')
                
                # If General, unit_type should be forced to 'cajetilla' (base) effectively
                if producto.tipo == 'general':
                    unit_type = 'cajetilla'

                # Determine multiplier
                mult = 1
                if unit_type == 'caja' and producto.tipo == 'cigarreria':
                    mult = producto.planchas_por_caja * producto.cajetillas_por_plancha
                elif unit_type == 'plancha' and producto.tipo == 'cigarreria':
                    mult = producto.cajetillas_por_plancha
                
                added_base_units = qty * mult
                variante.stock += added_base_units
                
                # Cost Calculation (Smart Pricing Logic requested)
                # "Para 'Cigarrería', calcula el costo de la cajetilla dividiendo el precio de la caja entre el multiplicador total."
                # This seems to apply if user enters "Costo Total" or "Costo Caja"?
                # If user provides total cost for the batch:
                costo_batch = float(data.get('costo_total', 0))
                if costo_batch > 0 and added_base_units > 0:
                    variante.precio_costo = costo_batch / added_base_units

                # Sync Siblings
                siblings = Variante.query.filter_by(producto_id=producto.id, origen=variante.origen, diseno=variante.diseno).all()
                for sib in siblings:
                    sib.stock = variante.stock
                    if costo_batch > 0:
                        sib.precio_costo = variante.precio_costo

            db.session.commit()
            return jsonify({'success': True, 'message': 'Producto actualizado'})

        else:
            # New Product Logic
            producto = Producto.query.filter_by(nombre=data['nombre']).first()
            if not producto:
                producto = Producto(
                    nombre=data['nombre'], 
                    categoria=data.get('categoria'),
                    tipo=data.get('tipo', 'general'),
                    planchas_por_caja=1,
                    cajetillas_por_plancha=1
                )
                if data.get('tipo') == 'cigarreria':
                    producto.planchas_por_caja = int(data.get('planchas_por_caja', 1))
                    producto.cajetillas_por_plancha = int(data.get('cajetillas_por_plancha', 1))

                db.session.add(producto)
                db.session.flush()
            else:
                # Update config if exists
                producto.tipo = data.get('tipo', 'general')
                if producto.tipo == 'cigarreria':
                    producto.planchas_por_caja = int(data.get('planchas_por_caja', 1))
                    producto.cajetillas_por_plancha = int(data.get('cajetillas_por_plancha', 1))
                else:
                    producto.planchas_por_caja = 1
                    producto.cajetillas_por_plancha = 1

            # Stock Calculation
            qty = int(data.get('stock', 0))
            unit_type = data.get('unit_type', 'caja')
            
            if producto.tipo == 'general':
                unit_type = 'cajetilla'

            mult = 1
            if unit_type == 'caja' and producto.tipo == 'cigarreria':
                mult = producto.planchas_por_caja * producto.cajetillas_por_plancha
            elif unit_type == 'plancha' and producto.tipo == 'cigarreria':
                mult = producto.cajetillas_por_plancha
                
            real_stock = qty * mult
            
            costo_total = float(data.get('costo_total', 0))
            unit_cost = 0
            if real_stock > 0 and costo_total > 0:
                unit_cost = costo_total / real_stock
            elif data.get('precio_costo'):
                 unit_cost = float(data.get('precio_costo'))

            nueva_variante = Variante(
                producto_id=producto.id,
                origen=data.get('origen'),
                diseno=data.get('diseno'),
                fecha_vencimiento=datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%d') if data.get('fecha_vencimiento') else None,
                stock=real_stock,
                precio_costo=unit_cost,
                precio_sugerido=float(data.get('precio_sugerido', 0)),
                precio_sugerido_plancha=float(data.get('precio_sugerido_plancha', 0)) if producto.tipo == 'cigarreria' else 0,
                precio_sugerido_caja=float(data.get('precio_sugerido_caja', 0)) if producto.tipo == 'cigarreria' else 0,
                multiplicador=1.0 
            )
            
            # Check siblings
            siblings = Variante.query.filter_by(producto_id=producto.id, origen=data.get('origen'), diseno=data.get('diseno')).all()
            if siblings:
                # Add to existing stock pool
                current_pool = siblings[0].stock
                new_pool = current_pool + real_stock
                nueva_variante.stock = new_pool
                
                # Update siblings
                for sib in siblings:
                    sib.stock = new_pool
                    # setup prices/config if we want to sync them?
            
            db.session.add(nueva_variante)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Mercadería cargada'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    variantes = db.session.query(Variante, Producto).join(Producto).all()
    data = []
    for variante, producto in variantes:
        data.append({
            'id': variante.id,
            'producto': producto.nombre,
            'categoria': producto.categoria,
            'origen': variante.origen,
            'diseno': variante.diseno,
            'stock': int(variante.stock // variante.multiplicador), # Visual stock
            'stock_real': variante.stock,
            'multiplicador': variante.multiplicador,
            'precio': variante.precio_sugerido,
            'precio_costo': variante.precio_costo,
            'fecha_vencimiento': variante.fecha_vencimiento.strftime('%Y-%m-%d') if variante.fecha_vencimiento else ''
        })
    return jsonify(data)

@app.route('/api/options', methods=['GET'])
def get_options():
    categorias = Categoria.query.all()
    origenes = Origen.query.all()
    return jsonify({
        'categorias': [c.nombre for c in categorias],
        'origenes': [o.nombre for o in origenes]
    })

@app.route('/api/category', methods=['POST'])
def add_category():
    nombre = request.json.get('nombre')
    if not nombre: return jsonify({'success': False}), 400
    if Categoria.query.filter_by(nombre=nombre).first():
        return jsonify({'success': True, 'message': 'Ya existe'})
    
    db.session.add(Categoria(nombre=nombre))
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/origin', methods=['POST'])
def add_origin():
    nombre = request.json.get('nombre')
    if not nombre: return jsonify({'success': False}), 400
    if Origen.query.filter_by(nombre=nombre).first():
        return jsonify({'success': True, 'message': 'Ya existe'})
        
    db.session.add(Origen(nombre=nombre))
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/category/<name>', methods=['DELETE'])
def delete_category(name):
    # Check usage
    if Producto.query.filter_by(categoria=name).count() > 0:
        return jsonify({'success': False, 'message': 'No se puede eliminar: Hay productos usando esta categoría.'}), 400
    
    cat = Categoria.query.filter_by(nombre=name).first()
    if cat:
        db.session.delete(cat)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/origin/<name>', methods=['DELETE'])
def delete_origin(name):
    # Check usage
    if Variante.query.filter_by(origen=name).count() > 0:
         return jsonify({'success': False, 'message': 'No se puede eliminar: Hay productos con este origen.'}), 400

    orig = Origen.query.filter_by(nombre=name).first()
    if orig:
        db.session.delete(orig)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/historial')
def history_page():
    return render_template('history.html')

@app.route('/reportes')
def reports_page():
    return render_template('reports.html')

@app.route('/api/history')
def api_history():
    date_filter = request.args.get('date')
    search = request.args.get('search')
    
    query = db.session.query(SaleDetail).join(Sale).join(Variante).join(Producto)
    
    if date_filter:
        query = query.filter(func.date(Sale.fecha) == date_filter)
        
    if search:
        query = query.filter(Producto.nombre.ilike(f'%{search}%'))
        
    # Order by date desc
    query = query.order_by(Sale.fecha.desc())
    
    # Limit to reasonable amount if no filter
    if not date_filter and not search:
        query = query.limit(100)
        
    details = query.all()
    results = []
    
    for d in details:
        profit = (d.precio_unitario - (d.costo_unitario or 0)) * d.cantidad
        results.append({
            'fecha': d.sale.fecha.strftime('%Y-%m-%d %H:%M'),
            'producto': d.variante.producto.nombre,
            'variante': f"{d.variante.origen} - {d.variante.diseno}",
            'metodo': d.sale.metodo_pago,
            'cantidad': d.cantidad,
            'precio_unitario': d.precio_unitario,
            'total_venta': d.precio_unitario * d.cantidad,
            'ganancia': profit
        })
        
    return jsonify(results)

@app.route('/api/reports')
def api_reports():
    # Use strict string comparison for SQLite dates (YYYY-MM-DD)
    today_str = date.today().strftime('%Y-%m-%d')
    yesterday_str = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 1. Cards (Today's metrics)
    # Income: Sum Sale.total
    today_income = db.session.query(func.sum(Sale.total)).filter(func.date(Sale.fecha) == today_str).scalar() or 0
    
    # Proft: Sum (Price - Cost) * Qty
    today_profit = db.session.query(
        func.sum((SaleDetail.precio_unitario - func.coalesce(SaleDetail.costo_unitario, 0)) * SaleDetail.cantidad)
    ).join(Sale).filter(func.date(Sale.fecha) == today_str).scalar() or 0
    
    # Avg Ticket: Income / Count
    sale_count = db.session.query(func.count(Sale.id)).filter(func.date(Sale.fecha) == today_str).scalar() or 0
    avg_ticket = (today_income / sale_count) if sale_count > 0 else 0

    # 2. Comparison Chart (Yesterday vs Today)
    yesterday_sales = db.session.query(func.sum(Sale.total)).filter(func.date(Sale.fecha) == yesterday_str).scalar() or 0
    
    # 3. Trend Chart (Current Month)
    month_sales = db.session.query(
        func.date(Sale.fecha), func.sum(Sale.total)
    ).filter(
        extract('year', Sale.fecha) == date.today().year,
        extract('month', Sale.fecha) == date.today().month
    ).group_by(func.date(Sale.fecha)).all()
    
    trend_labels = [row[0] for row in month_sales]
    trend_values = [row[1] for row in month_sales]
    
    # 4. Category Profit (Annual Profit Share)
    # Join path: SaleDetail -> Variante -> Producto
    cat_profit = db.session.query(
        Producto.categoria, 
        func.sum((SaleDetail.precio_unitario - func.coalesce(SaleDetail.costo_unitario, 0)) * SaleDetail.cantidad)
    ).select_from(SaleDetail).join(Variante).join(Producto).join(Sale).filter(
        extract('year', Sale.fecha) == date.today().year
    ).group_by(Producto.categoria).all()
    
    cat_labels = [row[0] or 'Sin Cat.' for row in cat_profit]
    cat_values = [row[1] for row in cat_profit]

    # 5. Top 5 Bestsellers (Volume)
    # Join path: SaleDetail -> Variante -> Producto
    top_products = db.session.query(
        Producto.nombre, func.sum(SaleDetail.cantidad)
    ).select_from(SaleDetail).join(Variante).join(Producto).group_by(Producto.nombre).order_by(
        func.sum(SaleDetail.cantidad).desc()
    ).limit(5).all()
    
    top_labels = [row[0] for row in top_products]
    top_values = [row[1] for row in top_products]

    # 6. Critical Stock (< 15)
    low_stock = db.session.query(Producto, Variante).join(Variante).filter(Variante.stock < 15).all()
    alerts = []
    for p, v in low_stock:
        var_name = f"{v.origen}"
        if v.diseno: var_name += f" - {v.diseno}"
        alerts.append({
            'producto': p.nombre,
            'variante': var_name, 
            'stock': int(v.stock)
        })
    
    return jsonify({
        'cards': {
            'income': float(today_income),
            'profit': float(today_profit),
            'avg_ticket': float(avg_ticket)
        },
        'charts': {
            'comparison': { 'yesterday': float(yesterday_sales), 'today': float(today_income) },
            'trend': { 'labels': trend_labels, 'values': trend_values },
            'categories': { 'labels': cat_labels, 'values': cat_values },
            'top5': { 'labels': top_labels, 'values': top_values }
        },
        'alerts': alerts
    })

def initialize_database():
    if not os.path.exists('marketflow.db'):
        with app.app_context():
            db.create_all()
            
            # Seed Defaults
            defaults_cat = ['Ropa', 'Accesorios', 'Juguetes', 'Cigarros', 'Otros']
            for name in defaults_cat:
                if not Categoria.query.filter_by(nombre=name).first():
                    db.session.add(Categoria(nombre=name))
            
            defaults_orig = ['China', 'Perú']
            for name in defaults_orig:
                if not Origen.query.filter_by(nombre=name).first():
                    db.session.add(Origen(nombre=name))
            
            db.session.commit()
            print("Database initialized and seeded.")

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
