"""Instancias de las extensiones de Flask.

Viven en su propio módulo, sin vincularse a ninguna aplicación, para que los
modelos y los blueprints puedan importarlas sin provocar importaciones
circulares. La fábrica `create_app` es la que las enlaza a una aplicación
concreta mediante `init_app`.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
