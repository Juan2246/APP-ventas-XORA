"""Rutas que devuelven HTML."""

from flask import Blueprint, render_template

bp = Blueprint("paginas", __name__)


@bp.route("/")
@bp.route("/billing")
def billing():
    """Punto de venta: es la pantalla de inicio del negocio."""
    return render_template("billing.html")


@bp.route("/inventario")
def inventory():
    return render_template("inventory.html")


@bp.route("/historial")
def history_page():
    return render_template("history.html")


@bp.route("/reportes")
def reports_page():
    return render_template("reports.html")
