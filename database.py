from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=True)
    tipo = db.Column(db.String(20), default='general') # 'general' or 'cigarreria'
    # Nested Packaging Configuration
    planchas_por_caja = db.Column(db.Integer, default=1)   # How many sheets in a box
    cajetillas_por_plancha = db.Column(db.Integer, default=1) # How many packs in a sheet
    variantes = db.relationship('Variante', backref='producto', lazy=True, cascade="all, delete-orphan")

class Variante(db.Model):
    __tablename__ = 'variantes'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    origen = db.Column(db.String(50)) # China/Perú
    diseno = db.Column(db.String(50)) # Mariposa/Embarazada
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    stock = db.Column(db.Integer, default=0) # Base units (Single packs/cajetillas)
    precio_costo = db.Column(db.Float, default=0.0) # Cost per base unit
    
    # Suggested Prices for each level
    precio_sugerido = db.Column(db.Float, default=0.0) # Price for Single Pack (Cajetilla)
    precio_sugerido_plancha = db.Column(db.Float, default=0.0)
    precio_sugerido_caja = db.Column(db.Float, default=0.0)
    
    multiplicador = db.Column(db.Float, default=1.0) # Deprecated/redundant? Kept for backward compat or custom overrides

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, default=0.0)
    metodo_pago = db.Column(db.String(50))
    details = db.relationship('SaleDetail', backref='sale', lazy=True, cascade="all, delete-orphan")

class SaleDetail(db.Model):
    __tablename__ = 'sale_details'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey('variantes.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Float, default=0.0)
    
    variante = db.relationship('Variante')

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

class Origen(db.Model):
    __tablename__ = 'origenes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

def init_db(app):
    with app.app_context():
        db.create_all()
