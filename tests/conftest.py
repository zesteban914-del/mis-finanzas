"""Configuración compartida de las pruebas.

Las pruebas usan SQLite en memoria en lugar de PostgreSQL para que sean
rápidas y no dependan de servicios externos. Las variables de entorno se
definen ANTES de importar la aplicación, porque se leen al importarla.
"""

import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ITERACIONES_HASH"] = "1000"  # cifrado rápido solo para pruebas

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SesionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Plan, RolUsuario, Usuario  # noqa: E402

CONTRASENA = "Clave12345"


@pytest.fixture()
def cliente_anonimo():
    """Cliente HTTP sin sesión, con una base de datos limpia por cada test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as cliente_de_pruebas:
        yield cliente_de_pruebas


@pytest.fixture()
def cliente(cliente_anonimo):
    """Cliente con la sesión de un usuario normal ya iniciada."""
    sesion = registrar(cliente_anonimo, "ana@correo.com", "Ana")
    cliente_anonimo.headers["Authorization"] = f"Bearer {sesion['access_token']}"
    return cliente_anonimo


def registrar(
    cliente, email, nombre="Usuario", categorias_iniciales=False, tipo="PERSONAL", **extra
) -> dict:
    respuesta = cliente.post(
        "/auth/registro",
        json={
            "tipo_cuenta": tipo,
            "nombre": nombre,
            "email": email,
            "contrasena": CONTRASENA,
            "acepta_terminos": True,
            "crear_categorias_iniciales": categorias_iniciales,
            **extra,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def encabezado(sesion: dict) -> dict:
    return {"Authorization": f"Bearer {sesion['access_token']}"}


def _modificar_usuario(email: str, **cambios) -> None:
    db = SesionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email).one()
        for campo, valor in cambios.items():
            setattr(usuario, campo, valor)
        db.commit()
    finally:
        db.close()


def convertir_en_admin(email: str) -> None:
    _modificar_usuario(email, rol=RolUsuario.ADMIN)


def activar_pro(email: str) -> None:
    _modificar_usuario(email, plan=Plan.PRO)


def crear_categoria(cliente, nombre="Comida", headers=None) -> int:
    respuesta = cliente.post("/categorias", json={"nombre": nombre}, headers=headers)
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def crear_movimiento(
    cliente,
    categoria_id,
    tipo="GASTO",
    monto=100.0,
    fecha="2026-11-10",
    descripcion="",
    headers=None,
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
        headers=headers,
    )
