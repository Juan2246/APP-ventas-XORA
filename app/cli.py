"""Comandos de línea de órdenes del proyecto."""

import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import Categoria, Origen

CATEGORIAS_INICIALES = ["Ropa", "Accesorios", "Juguetes", "Cigarros", "Otros"]
ORIGENES_INICIALES = ["China", "Perú"]


def inicializar_base_de_datos():
    """Crea las tablas que falten y siembra los catálogos básicos.

    Es idempotente: se puede ejecutar sobre una base ya poblada sin duplicar
    nada ni perder datos.
    """
    db.create_all()

    for nombre in CATEGORIAS_INICIALES:
        if not Categoria.query.filter_by(nombre=nombre).first():
            db.session.add(Categoria(nombre=nombre))

    for nombre in ORIGENES_INICIALES:
        if not Origen.query.filter_by(nombre=nombre).first():
            db.session.add(Origen(nombre=nombre))

    db.session.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Prepara la base de datos: crea las tablas y siembra los catálogos."""
    inicializar_base_de_datos()
    click.echo("Base de datos lista.")
