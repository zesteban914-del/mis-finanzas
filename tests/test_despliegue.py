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


def test_en_vercel_no_arranca_sin_clave_secreta(monkeypatch):
    monkeypatch.setattr(config, "EN_VERCEL", True)
    monkeypatch.setattr(config, "CLAVE_SECRETA", config.CLAVE_DE_DESARROLLO)

    with pytest.raises(RuntimeError, match="CLAVE_SECRETA"):
        with TestClient(app):
            pass
