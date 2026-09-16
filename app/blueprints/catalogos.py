"""Administración de categorías y orígenes.

Son listas auxiliares que alimentan los desplegables del inventario. Un
elemento en uso no se puede borrar: se responde 400 con el motivo, en lugar
de dejar productos apuntando a una categoría inexistente.
"""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Categoria, Origen, Producto, Variante

bp = Blueprint("catalogos", __name__)


@bp.route("/api/options", methods=["GET"])
def get_options():
    """Devuelve las opciones disponibles para los formularios del inventario."""
    return jsonify(
        {
            "categorias": [c.nombre for c in Categoria.query.all()],
            "origenes": [o.nombre for o in Origen.query.all()],
        }
    )


@bp.route("/api/category", methods=["POST"])
def add_category():
    nombre = request.json.get("nombre")
    if not nombre:
        return jsonify({"success": False}), 400

    if Categoria.query.filter_by(nombre=nombre).first():
        return jsonify({"success": True, "message": "Ya existe"})

    db.session.add(Categoria(nombre=nombre))
    db.session.commit()
    return jsonify({"success": True})


@bp.route("/api/origin", methods=["POST"])
def add_origin():
    nombre = request.json.get("nombre")
    if not nombre:
        return jsonify({"success": False}), 400

    if Origen.query.filter_by(nombre=nombre).first():
        return jsonify({"success": True, "message": "Ya existe"})

    db.session.add(Origen(nombre=nombre))
    db.session.commit()
    return jsonify({"success": True})


@bp.route("/api/category/<name>", methods=["DELETE"])
def delete_category(name):
    if Producto.query.filter_by(categoria=name).count() > 0:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "No se puede eliminar: Hay productos usando esta categoría.",
                }
            ),
            400,
        )

    categoria = Categoria.query.filter_by(nombre=name).first()
    if categoria:
        db.session.delete(categoria)
        db.session.commit()
    return jsonify({"success": True})


@bp.route("/api/origin/<name>", methods=["DELETE"])
def delete_origin(name):
    if Variante.query.filter_by(origen=name).count() > 0:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "No se puede eliminar: Hay productos con este origen.",
                }
            ),
            400,
        )

    origen = Origen.query.filter_by(nombre=name).first()
    if origen:
        db.session.delete(origen)
        db.session.commit()
    return jsonify({"success": True})
