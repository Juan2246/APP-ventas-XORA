"""Punto de venta: búsqueda de artículos y registro de la venta."""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Producto, Sale, SaleDetail, Variante
from app.servicios.unidades import (
    CAJA,
    CAJETILLA,
    PLANCHA,
    TIPO_GENERAL,
    cajetillas_por_caja,
    cajetillas_por_plancha,
    multiplicador,
    planchas_por_caja,
    separar_referencia,
)

bp = Blueprint("ventas", __name__)


def _nombre_base(producto, variante):
    """'Lucky (Perú - Mariposa)': nombre del producto más sus atributos."""
    atributos = [a for a in (variante.origen, variante.diseno) if a]
    sufijo = f" ({' - '.join(atributos)})" if atributos else ""
    return f"{producto.nombre}{sufijo}"


def _buscar_variantes(termino):
    """Variantes cuyo producto, origen o diseño contienen el término."""
    return (
        db.session.query(Variante, Producto)
        .join(Producto)
        .filter(
            Producto.nombre.ilike(f"%{termino}%")
            | Variante.origen.ilike(f"%{termino}%")
            | Variante.diseno.ilike(f"%{termino}%")
        )
        .all()
    )


@bp.route("/api/search_variants", methods=["GET"])
def search_variants_api():
    """Artículos vendibles que coinciden con la búsqueda del cajero.

    Un producto de cigarrería aparece hasta tres veces —caja, plancha y
    cajetilla— porque cada nivel es una opción de venta distinta, con su
    propio precio y su propio stock disponible. Los niveles sin precio
    definido no se ofrecen.
    """
    termino = request.args.get("q", "")
    if not termino:
        return jsonify([])

    articulos = []
    for variante, producto in _buscar_variantes(termino):
        nombre_base = _nombre_base(producto, variante)

        if producto.tipo == TIPO_GENERAL:
            articulos.append(
                {
                    "id": variante.id,
                    "nombre_completo": nombre_base,
                    "precio_sugerido": variante.precio_sugerido,
                    "stock": int(variante.stock),
                    "multiplicador": 1,
                }
            )
            continue

        por_plancha = cajetillas_por_plancha(producto)
        por_caja = cajetillas_por_caja(producto)
        planchas = planchas_por_caja(producto)

        if variante.precio_sugerido_caja > 0:
            articulos.append(
                {
                    "id": f"{variante.id}_{CAJA}",
                    "nombre_completo": f"{nombre_base} - CAJA x{planchas} Planchas",
                    "precio_sugerido": variante.precio_sugerido_caja,
                    "stock": int(variante.stock // por_caja),
                    "multiplicador": por_caja,
                }
            )

        if variante.precio_sugerido_plancha > 0:
            articulos.append(
                {
                    "id": f"{variante.id}_{PLANCHA}",
                    "nombre_completo": f"{nombre_base} - PLANCHA x{por_plancha} Cajetillas",
                    "precio_sugerido": variante.precio_sugerido_plancha,
                    "stock": int(variante.stock // por_plancha),
                    "multiplicador": por_plancha,
                }
            )

        # La cajetilla es la unidad base: siempre se puede vender suelta.
        articulos.append(
            {
                "id": f"{variante.id}_{CAJETILLA}",
                "nombre_completo": f"{nombre_base} - CAJETILLA",
                "precio_sugerido": variante.precio_sugerido,
                "stock": int(variante.stock),
                "multiplicador": 1,
            }
        )

    return jsonify(articulos)


def _variantes_hermanas(variante):
    """Filas que representan el mismo artículo físico.

    El histórico dejó variantes duplicadas para un mismo producto, origen y
    diseño. Comparten existencias reales, así que su stock se mantiene
    sincronizado para que el inventario no se contradiga.
    """
    return (
        db.session.query(Variante)
        .filter_by(
            producto_id=variante.producto_id,
            origen=variante.origen,
            diseno=variante.diseno,
        )
        .all()
    )


@bp.route("/process_sale", methods=["POST"])
def process_sale():
    """Registra una venta y descuenta el stock de cada línea.

    Todo ocurre en una sola transacción: si una línea no tiene existencias
    suficientes, se revierte la venta completa y no se descuenta nada.
    """
    datos = request.json
    try:
        venta = Sale(total=datos["total"], metodo_pago=datos["metodo_pago"])
        db.session.add(venta)
        db.session.flush()

        for linea in datos["items"]:
            id_variante, unidad = separar_referencia(linea["id"])

            variante = db.session.get(Variante, id_variante)
            if not variante:
                raise Exception(f"Variante {linea['id']} no encontrada")

            producto = variante.producto
            factor = multiplicador(producto, unidad)
            unidades_base = linea["cantidad"] * factor

            if variante.stock < unidades_base:
                disponible = int(variante.stock // factor)
                raise Exception(
                    f"Stock insuficiente para {producto.nombre} ({unidad}). "
                    f"Disponible: {disponible}"
                )

            stock_restante = variante.stock - unidades_base
            for hermana in _variantes_hermanas(variante):
                hermana.stock = stock_restante

            db.session.add(
                SaleDetail(
                    sale_id=venta.id,
                    variante_id=variante.id,
                    cantidad=linea["cantidad"],
                    precio_unitario=linea["precio"],
                    # El coste se escala a la unidad vendida para que la
                    # ganancia se calcule restando precio menos coste.
                    costo_unitario=variante.precio_costo * factor,
                )
            )

        db.session.commit()
        return jsonify({"success": True, "message": "Venta procesada correctamente"})

    except Exception as error:
        db.session.rollback()
        return jsonify({"success": False, "message": str(error)}), 400
