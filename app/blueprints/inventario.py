"""Inventario: consulta del stock y alta, edición y reposición de mercadería."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Producto, Variante
from app.servicios.unidades import (
    CAJA,
    CAJETILLA,
    TIPO_CIGARRERIA,
    TIPO_GENERAL,
    multiplicador,
    normalizar_unidad,
)

bp = Blueprint("inventario", __name__)


@bp.route("/api/search", methods=["GET"])
def search_products():
    """Variantes del inventario, filtradas por nombre, origen o diseño.

    Sin término de búsqueda devuelve el inventario completo: la pantalla lo
    necesita entero para calcular sus totales.
    """
    termino = request.args.get("q", "")

    consulta = db.session.query(Variante, Producto).join(Producto)
    if termino:
        consulta = consulta.filter(
            Producto.nombre.ilike(f"%{termino}%")
            | Variante.origen.ilike(f"%{termino}%")
            | Variante.diseno.ilike(f"%{termino}%")
        )

    return jsonify(
        [
            {
                "id": variante.id,
                "nombre": producto.nombre,
                "categoria": producto.categoria,
                "origen": variante.origen,
                "diseno": variante.diseno,
                "precio_sugerido": variante.precio_sugerido,
                "stock": variante.stock,
                "planchas_por_caja": producto.planchas_por_caja,
                "cajetillas_por_plancha": producto.cajetillas_por_plancha,
                "precio_sugerido_plancha": variante.precio_sugerido_plancha,
                "precio_sugerido_caja": variante.precio_sugerido_caja,
                "precio_costo": variante.precio_costo,
            }
            for variante, producto in consulta.all()
        ]
    )


@bp.route("/api/inventory", methods=["GET"])
def get_inventory():
    """Inventario completo para la tabla de existencias."""
    return jsonify(
        [
            {
                "id": variante.id,
                "producto": producto.nombre,
                "categoria": producto.categoria,
                "origen": variante.origen,
                "diseno": variante.diseno,
                "stock": int(variante.stock // variante.multiplicador),
                "stock_real": variante.stock,
                "multiplicador": variante.multiplicador,
                "precio": variante.precio_sugerido,
                "precio_costo": variante.precio_costo,
                "fecha_vencimiento": (
                    variante.fecha_vencimiento.strftime("%Y-%m-%d")
                    if variante.fecha_vencimiento
                    else ""
                ),
            }
            for variante, producto in db.session.query(Variante, Producto)
            .join(Producto)
            .all()
        ]
    )


def _aplicar_empaquetado(producto, datos):
    """Fija el empaquetado del producto según su tipo.

    Un producto general no tiene niveles: sus factores vuelven a 1 para que un
    cambio de cigarrería a general no deje multiplicadores viejos activos.
    """
    producto.tipo = datos.get("tipo", TIPO_GENERAL)
    if producto.tipo == TIPO_CIGARRERIA:
        producto.planchas_por_caja = int(datos.get("planchas_por_caja", 1))
        producto.cajetillas_por_plancha = int(datos.get("cajetillas_por_plancha", 1))
    else:
        producto.planchas_por_caja = 1
        producto.cajetillas_por_plancha = 1


def _hermanas(producto_id, origen, diseno):
    """Variantes que comparten existencias reales (mismo artículo físico)."""
    return Variante.query.filter_by(
        producto_id=producto_id, origen=origen, diseno=diseno
    ).all()


def _editar(producto, variante, datos):
    """Actualiza los datos descriptivos y los precios. No toca el stock."""
    producto.nombre = datos["nombre"]
    producto.categoria = datos.get("categoria")
    _aplicar_empaquetado(producto, datos)

    variante.origen = datos.get("origen")
    variante.diseno = datos.get("diseno")
    variante.precio_sugerido = float(datos.get("precio_sugerido", 0))

    if producto.tipo == TIPO_CIGARRERIA:
        variante.precio_sugerido_plancha = float(datos.get("precio_sugerido_plancha", 0))
        variante.precio_sugerido_caja = float(datos.get("precio_sugerido_caja", 0))
    else:
        variante.precio_sugerido_plancha = 0
        variante.precio_sugerido_caja = 0

    variante.precio_costo = float(datos.get("precio_costo", 0))


def _reponer(producto, variante, datos):
    """Suma mercadería al stock y recalcula el coste unitario del lote.

    La cantidad llega en la unidad que compró el negocio (cajas, planchas o
    cajetillas) y se convierte a unidad base. Si se indica el coste total del
    lote, el coste por unidad se deriva de él.
    """
    cantidad = int(datos.get("stock", 0))
    unidad = normalizar_unidad(producto, datos.get("unit_type", CAJETILLA))
    unidades_base = cantidad * multiplicador(producto, unidad)

    variante.stock += unidades_base

    costo_lote = float(datos.get("costo_total", 0))
    if costo_lote > 0 and unidades_base > 0:
        variante.precio_costo = costo_lote / unidades_base

    for hermana in _hermanas(producto.id, variante.origen, variante.diseno):
        hermana.stock = variante.stock
        if costo_lote > 0:
            hermana.precio_costo = variante.precio_costo


def _crear(datos):
    """Da de alta mercadería, reutilizando el producto si el nombre ya existe."""
    producto = Producto.query.filter_by(nombre=datos["nombre"]).first()
    if not producto:
        producto = Producto(nombre=datos["nombre"], categoria=datos.get("categoria"))
        _aplicar_empaquetado(producto, datos)
        db.session.add(producto)
        db.session.flush()
    else:
        _aplicar_empaquetado(producto, datos)

    cantidad = int(datos.get("stock", 0))
    unidad = normalizar_unidad(producto, datos.get("unit_type", CAJA))
    unidades_base = cantidad * multiplicador(producto, unidad)

    costo_lote = float(datos.get("costo_total", 0))
    if unidades_base > 0 and costo_lote > 0:
        costo_unitario = costo_lote / unidades_base
    elif datos.get("precio_costo"):
        costo_unitario = float(datos.get("precio_costo"))
    else:
        costo_unitario = 0

    es_cigarreria = producto.tipo == TIPO_CIGARRERIA
    variante = Variante(
        producto_id=producto.id,
        origen=datos.get("origen"),
        diseno=datos.get("diseno"),
        fecha_vencimiento=(
            datetime.strptime(datos["fecha_vencimiento"], "%Y-%m-%d")
            if datos.get("fecha_vencimiento")
            else None
        ),
        stock=unidades_base,
        precio_costo=costo_unitario,
        precio_sugerido=float(datos.get("precio_sugerido", 0)),
        precio_sugerido_plancha=(
            float(datos.get("precio_sugerido_plancha", 0)) if es_cigarreria else 0
        ),
        precio_sugerido_caja=(
            float(datos.get("precio_sugerido_caja", 0)) if es_cigarreria else 0
        ),
        multiplicador=1.0,
    )

    # Si ya existía este artículo, las existencias se acumulan en un único
    # pool compartido por todas sus filas.
    hermanas = _hermanas(producto.id, datos.get("origen"), datos.get("diseno"))
    if hermanas:
        pool = hermanas[0].stock + unidades_base
        variante.stock = pool
        for hermana in hermanas:
            hermana.stock = pool

    db.session.add(variante)


@bp.route("/api/product", methods=["POST"])
def manage_product():
    """Alta, edición o reposición de mercadería.

    La operación la decide el cuerpo de la petición: sin `variant_id` es un
    alta; con él, `action_type` distingue entre editar y reponer.
    """
    datos = request.json
    try:
        id_variante = datos.get("variant_id")

        if id_variante:
            variante = db.session.get(Variante, id_variante)
            if not variante:
                return (
                    jsonify({"success": False, "message": "Variante no encontrada"}),
                    404,
                )

            accion = datos.get("action_type", "new")
            if accion == "edit":
                _editar(variante.producto, variante, datos)
            elif accion == "restock":
                _reponer(variante.producto, variante, datos)

            db.session.commit()
            return jsonify({"success": True, "message": "Producto actualizado"})

        _crear(datos)
        db.session.commit()
        return jsonify({"success": True, "message": "Mercadería cargada"})

    except Exception as error:
        db.session.rollback()
        return jsonify({"success": False, "message": str(error)}), 400
