"""Configuración por entorno.

Mantener la configuración fuera del código de la aplicación permite arrancar
la misma aplicación en desarrollo, en pruebas y en producción sin tocar una
sola línea de lógica. Ningún secreto se escribe aquí: se leen del entorno.
"""

import os
import secrets


class Config:
    """Valores comunes a todos los entornos."""

    def __init__(self):
        clave = os.environ.get("SECRET_KEY", "").strip()
        if len(clave) < 32 or clave.startswith(("clave-de-desarrollo", "cambia")):
            raise RuntimeError(
                "SECRET_KEY debe definirse con un valor aleatorio de al menos 32 caracteres."
            )
        self.SECRET_KEY = clave
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///marketflow.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Unidades de venta de los productos de cigarrería
    STOCK_CRITICO = 15          # umbral de la alerta de inventario bajo
    LIMITE_HISTORIAL = 100      # filas que devuelve el historial sin filtros


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    def __init__(self):
        # Las pruebas nunca usan claves ni bases del entorno real.
        self.SECRET_KEY = secrets.token_urlsafe(48)
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
