"""Configuración por entorno.

Mantener la configuración fuera del código de la aplicación permite arrancar
la misma aplicación en desarrollo, en pruebas y en producción sin tocar una
sola línea de lógica. Ningún secreto se escribe aquí: se leen del entorno.
"""

import os


class Config:
    """Valores comunes a todos los entornos."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-de-desarrollo-no-usar-en-produccion")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///marketflow.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Unidades de venta de los productos de cigarrería
    STOCK_CRITICO = 15          # umbral de la alerta de inventario bajo
    LIMITE_HISTORIAL = 100      # filas que devuelve el historial sin filtros


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False

    def __init__(self):
        if os.environ.get("SECRET_KEY") is None:
            raise RuntimeError(
                "SECRET_KEY no está definida. En producción debe proporcionarse "
                "por variable de entorno."
            )


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
