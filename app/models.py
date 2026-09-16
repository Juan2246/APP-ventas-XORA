"""Modelo de datos.

Un producto agrupa variantes (mismo artículo en distinto origen o diseño).
El stock se lleva siempre en la **unidad base** —la cajetilla para los
productos de cigarrería, la unidad suelta para el resto—, y las ventas por
plancha o por caja se convierten a esa unidad antes de descontar. Así el
inventario tiene una sola fuente de verdad.
"""

from datetime import datetime

from app.extensions import db


class Producto(db.Model):
    """Artículo del catálogo y su configuración de empaquetado."""

    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=True)
    tipo = db.Column(db.String(20), default="general")  # 'general' | 'cigarreria'

    # Empaquetado anidado: caja > plancha > cajetilla
    planchas_por_caja = db.Column(db.Integer, default=1)
    cajetillas_por_plancha = db.Column(db.Integer, default=1)

    variantes = db.relationship(
        "Variante", backref="producto", lazy=True, cascade="all, delete-orphan"
    )


class Variante(db.Model):
    """Presentación concreta de un producto: su origen, diseño, stock y precios."""

    __tablename__ = "variantes"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    origen = db.Column(db.String(50))          # China / Perú
    diseno = db.Column(db.String(50))          # Mariposa / Embarazada
    fecha_vencimiento = db.Column(db.Date, nullable=True)

    stock = db.Column(db.Integer, default=0)          # siempre en unidad base
    precio_costo = db.Column(db.Float, default=0.0)   # coste de la unidad base

    # Precio sugerido para cada nivel de empaquetado
    precio_sugerido = db.Column(db.Float, default=0.0)          # cajetilla / unidad
    precio_sugerido_plancha = db.Column(db.Float, default=0.0)
    precio_sugerido_caja = db.Column(db.Float, default=0.0)

    # Se conserva por compatibilidad con los registros anteriores al
    # empaquetado anidado, que guardaban aquí su factor de conversión.
    multiplicador = db.Column(db.Float, default=1.0)


class Sale(db.Model):
    """Cabecera de una venta."""

    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, default=0.0)
    metodo_pago = db.Column(db.String(50))

    details = db.relationship(
        "SaleDetail", backref="sale", lazy=True, cascade="all, delete-orphan"
    )


class SaleDetail(db.Model):
    """Línea de una venta.

    `precio_unitario` y `costo_unitario` están expresados en la unidad
    efectivamente vendida (caja, plancha o cajetilla), no en la unidad base,
    de modo que la ganancia sale de restarlos directamente.
    """

    __tablename__ = "sale_details"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey("variantes.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Float, default=0.0)

    variante = db.relationship("Variante")


class Categoria(db.Model):
    """Categoría del catálogo, administrable desde el inventario."""

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)


class Origen(db.Model):
    """Procedencia de la mercadería, administrable desde el inventario."""

    __tablename__ = "origenes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
