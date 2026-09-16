"""Historial de ventas, línea a línea."""

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func

from app.extensions import db
from app.models import Producto, Sale, SaleDetail, Variante

bp = Blueprint("historial", __name__)


@bp.route("/api/history")
def api_history():
    """Detalle de ventas con su ganancia, de la más reciente a la más antigua.

    Sin filtros se recorta a las últimas filas: el historial completo crece
    sin límite y la pantalla no lo necesita entero.
    """
    fecha = request.args.get("date")
    busqueda = request.args.get("search")

    consulta = db.session.query(SaleDetail).join(Sale).join(Variante).join(Producto)

    if fecha:
        consulta = consulta.filter(func.date(Sale.fecha) == fecha)
    if busqueda:
        consulta = consulta.filter(Producto.nombre.ilike(f"%{busqueda}%"))

    consulta = consulta.order_by(Sale.fecha.desc())

    if not fecha and not busqueda:
        consulta = consulta.limit(current_app.config["LIMITE_HISTORIAL"])

    return jsonify(
        [
            {
                "fecha": linea.sale.fecha.strftime("%Y-%m-%d %H:%M"),
                "producto": linea.variante.producto.nombre,
                "variante": f"{linea.variante.origen} - {linea.variante.diseno}",
                "metodo": linea.sale.metodo_pago,
                "cantidad": linea.cantidad,
                "precio_unitario": linea.precio_unitario,
                "total_venta": linea.precio_unitario * linea.cantidad,
                "ganancia": (linea.precio_unitario - (linea.costo_unitario or 0))
                * linea.cantidad,
            }
            for linea in consulta.all()
        ]
    )
