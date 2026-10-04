"""Fábrica de la aplicación.

Crear la aplicación dentro de una función, en vez de a nivel de módulo,
permite levantar instancias con configuraciones distintas —desarrollo,
pruebas, producción— sin tocar el código, y evita que importar el paquete
tenga efectos secundarios.
"""

import os

from flask import Flask
from werkzeug.utils import import_string

from app.config import CONFIGS, Config
from app.extensions import db


def create_app(config=None):
    """Construye y devuelve una aplicación Flask lista para servir.

    :param config: clase de configuración, ruta a una ("app.config.TestingConfig")
        o nombre de entorno ("development", "testing", "production"). Si se
        omite se usa la variable de entorno ``FLASK_ENV``, y en su defecto
        el entorno de desarrollo.
    """
    app = Flask(__name__)
    app.config.from_object(_resolver_config(config))

    db.init_app(app)
    _registrar_blueprints(app)
    _registrar_comandos(app)

    return app


def _resolver_config(config):
    """Traduce el argumento recibido a un objeto de configuración."""
    if config is None:
        config = os.environ.get("FLASK_ENV", "development")
    if isinstance(config, str):
        config = CONFIGS[config] if config in CONFIGS else import_string(config)
    if isinstance(config, type) and issubclass(config, Config):
        return config()
    return config


def _registrar_blueprints(app):
    """Engancha cada área funcional a la aplicación.

    Las rutas se declaran completas dentro de cada blueprint, sin
    ``url_prefix``, para que las URL que consume el front no cambien.
    """
    from app.blueprints import (
        catalogos,
        historial,
        inventario,
        paginas,
        reportes,
        ventas,
    )

    for modulo in (paginas, ventas, inventario, catalogos, historial, reportes):
        app.register_blueprint(modulo.bp)


def _registrar_comandos(app):
    """Añade los comandos de `flask` propios del proyecto."""
    from app.cli import init_db_command

    app.cli.add_command(init_db_command)
