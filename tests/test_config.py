"""El arranque rechaza claves ausentes y las pruebas aíslan datos privados."""

import secrets

import pytest

from app import create_app
from app.config import ProductionConfig


@pytest.mark.parametrize("entorno", ["development", "production"])
@pytest.mark.parametrize("clave", [None, "", "   ", "corta"])
def test_rechaza_clave_invalida(monkeypatch, entorno, clave):
    if clave is None:
        monkeypatch.delenv("SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("SECRET_KEY", clave)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(entorno)


def test_lee_la_clave_al_crear_cada_aplicacion(monkeypatch):
    primera, segunda = secrets.token_urlsafe(48), secrets.token_urlsafe(48)
    monkeypatch.setenv("SECRET_KEY", primera)
    assert create_app("production").secret_key == primera
    monkeypatch.setenv("SECRET_KEY", segunda)
    assert create_app("production").secret_key == segunda


def test_pruebas_ignoran_base_y_clave_del_entorno(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///no-usar.db")
    monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(48))
    primera = create_app("testing")
    segunda = create_app("testing")
    assert primera.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    assert primera.secret_key != segunda.secret_key


@pytest.mark.parametrize("config", [ProductionConfig, "app.config.ProductionConfig"])
def test_clase_y_ruta_tambien_validan_clave(monkeypatch, config):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(config)
