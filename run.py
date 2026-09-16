"""Arranque en desarrollo.

    python run.py

Prepara la base de datos si hace falta y levanta el servidor de desarrollo.
En producción se usa `wsgi.py` con gunicorn, no este archivo.
"""

from app import create_app
from app.cli import inicializar_base_de_datos

app = create_app("development")

if __name__ == "__main__":
    with app.app_context():
        inicializar_base_de_datos()
    app.run(debug=True)
