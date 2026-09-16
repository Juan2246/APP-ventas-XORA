"""Panel de reportes: métricas del día, tendencias y alertas de stock.

La ganancia se calcula siempre igual: ``(precio - coste) x cantidad`` sobre
las líneas de venta, porque ahí el coste ya está escalado a la unidad que se
vendió. Sumar sobre la cabecera de la venta daría el ingreso, no el margen.
"""

from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify
from sqlalchemy import extract, func

from app.extensions import db
from app.models import Producto, Sale, SaleDetail, Variante

bp = Blueprint("reportes", __name__)

# Expresión de la ganancia de una línea de venta, reutilizada en las consultas.
GANANCIA = (
    SaleDetail.precio_unitario - func.coalesce(SaleDetail.costo_unitario, 0)
) * SaleDetail.cantidad


def _ingreso_del_dia(dia):
    """Suma de las ventas de una fecha (comparación textual, como guarda SQLite)."""
    return (
        db.session.query(func.sum(Sale.total))
        .filter(func.date(Sale.fecha) == dia)
        .scalar()
        or 0
    )


@bp.route("/api/reports")
def api_reports():
    hoy = date.today().strftime("%Y-%m-%d")
    ayer = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    # --- Tarjetas del día ---------------------------------------------------
    ingreso_hoy = _ingreso_del_dia(hoy)

    ganancia_hoy = (
        db.session.query(func.sum(GANANCIA))
        .join(Sale)
        .filter(func.date(Sale.fecha) == hoy)
        .scalar()
        or 0
    )

    num_ventas = (
        db.session.query(func.count(Sale.id))
        .filter(func.date(Sale.fecha) == hoy)
        .scalar()
        or 0
    )
    ticket_promedio = (ingreso_hoy / num_ventas) if num_ventas > 0 else 0

    # --- Tendencia del mes en curso -----------------------------------------
    ventas_del_mes = (
        db.session.query(func.date(Sale.fecha), func.sum(Sale.total))
        .filter(
            extract("year", Sale.fecha) == date.today().year,
            extract("month", Sale.fecha) == date.today().month,
        )
        .group_by(func.date(Sale.fecha))
        .all()
    )

    # --- Reparto anual de la ganancia por categoría --------------------------
    ganancia_por_categoria = (
        db.session.query(Producto.categoria, func.sum(GANANCIA))
        .select_from(SaleDetail)
        .join(Variante)
        .join(Producto)
        .join(Sale)
        .filter(extract("year", Sale.fecha) == date.today().year)
        .group_by(Producto.categoria)
        .all()
    )

    # --- Los cinco más vendidos por volumen ----------------------------------
    mas_vendidos = (
        db.session.query(Producto.nombre, func.sum(SaleDetail.cantidad))
        .select_from(SaleDetail)
        .join(Variante)
        .join(Producto)
        .group_by(Producto.nombre)
        .order_by(func.sum(SaleDetail.cantidad).desc())
        .limit(5)
        .all()
    )

    # --- Alertas de stock crítico --------------------------------------------
    umbral = current_app.config["STOCK_CRITICO"]
    criticos = (
        db.session.query(Producto, Variante)
        .join(Variante)
        .filter(Variante.stock < umbral)
        .all()
    )

    alertas = []
    for producto, variante in criticos:
        nombre_variante = f"{variante.origen}"
        if variante.diseno:
            nombre_variante += f" - {variante.diseno}"
        alertas.append(
            {
                "producto": producto.nombre,
                "variante": nombre_variante,
                "stock": int(variante.stock),
            }
        )

    return jsonify(
        {
            "cards": {
                "income": float(ingreso_hoy),
                "profit": float(ganancia_hoy),
                "avg_ticket": float(ticket_promedio),
            },
            "charts": {
                "comparison": {
                    "yesterday": float(_ingreso_del_dia(ayer)),
                    "today": float(ingreso_hoy),
                },
                "trend": {
                    "labels": [fila[0] for fila in ventas_del_mes],
                    "values": [fila[1] for fila in ventas_del_mes],
                },
                "categories": {
                    "labels": [fila[0] or "Sin Cat." for fila in ganancia_por_categoria],
                    "values": [fila[1] for fila in ganancia_por_categoria],
                },
                "top5": {
                    "labels": [fila[0] for fila in mas_vendidos],
                    "values": [fila[1] for fila in mas_vendidos],
                },
            },
            "alerts": alertas,
        }
    )
