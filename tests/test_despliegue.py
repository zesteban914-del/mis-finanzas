"""Ajustes para publicar la app en la nube (Vercel + Neon)."""

import pytest
from fastapi.testclient import TestClient

from app import config
from app.database import SesionLocal, normalizar_url
from app.datos_demo import cargar_datos_si_vacia
from app.main import app
from app.models import RolUsuario, Usuario


@pytest.mark.parametrize(
    ("entrada", "esperada"),
    [
        ("postgres://u:c@host/db?sslmode=require", "postgresql+psycopg2://u:c@host/db?sslmode=require"),
        ("postgresql://u:c@host/db", "postgresql+psycopg2://u:c@host/db"),
        ("postgresql+psycopg2://u:c@host/db", "postgresql+psycopg2://u:c@host/db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_normaliza_las_urls_de_los_proveedores(entrada, esperada):
    assert normalizar_url(entrada) == esperada


def test_carga_la_demostracion_solo_si_la_base_esta_vacia(cliente_anonimo):
    primera = cargar_datos_si_vacia()
    segunda = cargar_datos_si_vacia()

    db = SesionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == "admin@misfinanzas.test").one()
        total = db.query(Usuario).count()
    finally:
        db.close()

    assert primera is True and segunda is False
    assert admin.rol == RolUsuario.ADMIN
    assert total == 6


def test_sin_variable_genera_una_clave_y_la_reutiliza(cliente_anonimo, monkeypatch):
    monkeypatch.delenv("CLAVE_SECRETA", raising=False)
    primera = config.CLAVE_SECRETA  # generada al arrancar el cliente de la prueba

    with TestClient(app):  # segundo arranque: debe leer la misma clave de la base
        segunda = config.CLAVE_SECRETA

    assert primera == segunda
    assert primera != config.CLAVE_DE_DESARROLLO
    assert len(primera) >= 40


def test_la_variable_de_entorno_tiene_prioridad(cliente_anonimo, monkeypatch):
    monkeypatch.setenv("CLAVE_SECRETA", "clave-definida-en-vercel")

    with TestClient(app):
        clave = config.CLAVE_SECRETA

    assert clave == "clave-definida-en-vercel"
