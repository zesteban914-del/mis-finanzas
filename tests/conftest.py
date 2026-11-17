"""Configuración compartida de las pruebas.

Las pruebas usan SQLite en memoria en lugar de PostgreSQL para que sean
rápidas y no dependan de servicios externos. La variable DATABASE_URL se
define ANTES de importar la aplicación, porque app/database.py la lee al
momento del import.
"""

import os

os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def cliente():
    """Cliente HTTP de prueba con una base de datos limpia por cada test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as cliente_de_pruebas:
        yield cliente_de_pruebas


def crear_categoria(cliente, nombre="Comida") -> int:
    respuesta = cliente.post("/categorias", json={"nombre": nombre})
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def crear_movimiento(
    cliente,
    categoria_id,
    tipo="GASTO",
    monto=100.0,
    fecha="2026-11-10",
    descripcion="",
):
    return cliente.post(
        "/movimientos",
        json={
            "tipo": tipo,
            "monto": monto,
            "fecha": fecha,
            "descripcion": descripcion,
            "categoria_id": categoria_id,
        },
    )
