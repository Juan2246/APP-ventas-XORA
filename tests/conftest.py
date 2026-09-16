"""Fixtures compartidas por la batería de pruebas.

Cada prueba recibe una base de datos en memoria recién creada y sembrada, de
modo que el orden en que se ejecuten no cambia el resultado.
"""

import pytest

from app import create_app
from app.extensions import db
from app.models import Categoria, Origen, Producto, Variante


@pytest.fixture
def app():
    """Aplicación configurada para pruebas, con la base de datos en memoria."""
    aplicacion = create_app("testing")
    with aplicacion.app_context():
        db.create_all()
        yield aplicacion
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente HTTP que llama a la aplicación sin levantar un servidor."""
    return app.test_client()


@pytest.fixture
def catalogo(app):
    """Catálogo mínimo: una prenda suelta y un producto de cigarrería.

    El de cigarrería usa 5 planchas por caja y 10 cajetillas por plancha, así
    que una caja equivale a 50 cajetillas. Es el caso que ejercita la
    conversión de unidades.
    """
    db.session.add_all(
        [
            Categoria(nombre="Ropa"),
            Categoria(nombre="Cigarros"),
            Origen(nombre="China"),
            Origen(nombre="Perú"),
        ]
    )

    polo = Producto(
        nombre="Polo básico",
        categoria="Ropa",
        tipo="general",
        planchas_por_caja=1,
        cajetillas_por_plancha=1,
    )
    cigarro = Producto(
        nombre="Lucky",
        categoria="Cigarros",
        tipo="cigarreria",
        planchas_por_caja=5,
        cajetillas_por_plancha=10,
    )
    db.session.add_all([polo, cigarro])
    db.session.flush()

    variante_polo = Variante(
        producto_id=polo.id,
        origen="China",
        diseno="Mariposa",
        stock=40,
        precio_costo=5.0,
        precio_sugerido=12.0,
        multiplicador=1.0,
    )
    variante_cigarro = Variante(
        producto_id=cigarro.id,
        origen="Perú",
        stock=500,
        precio_costo=1.0,
        precio_sugerido=4.0,
        precio_sugerido_plancha=38.0,
        precio_sugerido_caja=180.0,
        multiplicador=1.0,
    )
    db.session.add_all([variante_polo, variante_cigarro])
    db.session.commit()

    return {
        "polo": polo,
        "cigarro": cigarro,
        "variante_polo": variante_polo.id,
        "variante_cigarro": variante_cigarro.id,
    }
