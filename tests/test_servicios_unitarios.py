"""Pruebas unitarias: llaman a la capa de servicios directamente, sin HTTP.

Demuestran que las reglas de negocio no dependen de FastAPI.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.database import Base, SesionLocal, engine
from app.models import TipoMovimiento
from app.repositories import RepositorioUsuarios
from app.schemas import CategoriaCrear, MovimientoCrear, PresupuestoCrear
from app.services import (
    ServicioCategorias,
    ServicioMovimientos,
    ServicioPresupuestos,
    ServicioReportes,
)
from app.services.excepciones import ConflictoDeDatos, ErrorDeValidacion


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    sesion = SesionLocal()
    yield sesion
    sesion.close()


@pytest.fixture()
def usuario(db):
    return RepositorioUsuarios(db).crear(
        nombre="Ana", email="ana@correo.com", contrasena_hash="hash-de-prueba"
    )


def nuevo_movimiento(categoria_id, tipo=TipoMovimiento.GASTO, monto="100", fecha=None):
    return MovimientoCrear(
        tipo=tipo,
        monto=Decimal(monto),
        fecha=fecha or date(2026, 11, 1),
        categoria_id=categoria_id,
    )


def test_servicio_rechaza_monto_cero(db, usuario):
    categoria = ServicioCategorias(db, usuario).crear(CategoriaCrear(nombre="Comida"))

    with pytest.raises(ErrorDeValidacion, match="mayor que 0"):
        ServicioMovimientos(db, usuario).crear(nuevo_movimiento(categoria.id, monto="0"))


def test_servicio_rechaza_fecha_futura(db, usuario):
    categoria = ServicioCategorias(db, usuario).crear(CategoriaCrear(nombre="Comida"))
    manana = date.today() + timedelta(days=1)

    with pytest.raises(ErrorDeValidacion, match="futura"):
        ServicioMovimientos(db, usuario).crear(nuevo_movimiento(categoria.id, fecha=manana))


def test_servicio_calcula_saldo(db, usuario):
    categoria = ServicioCategorias(db, usuario).crear(CategoriaCrear(nombre="General"))
    movimientos = ServicioMovimientos(db, usuario)
    movimientos.crear(nuevo_movimiento(categoria.id, TipoMovimiento.INGRESO, "1000"))
    movimientos.crear(nuevo_movimiento(categoria.id, TipoMovimiento.GASTO, "250.75"))

    saldo = ServicioReportes(db, usuario).saldo()

    assert saldo.saldo == Decimal("749.25")


def test_servicio_detecta_presupuesto_superado(db, usuario):
    categoria = ServicioCategorias(db, usuario).crear(CategoriaCrear(nombre="Comida"))
    presupuestos = ServicioPresupuestos(db, usuario)
    presupuestos.crear(PresupuestoCrear(mes="2026-11", limite=Decimal("100")))

    _, alerta = ServicioMovimientos(db, usuario).crear(
        nuevo_movimiento(categoria.id, monto="150")
    )

    assert alerta is not None
    assert presupuestos.estado("2026-11").excedido is True


def test_servicio_no_elimina_categoria_con_movimientos(db, usuario):
    servicio = ServicioCategorias(db, usuario)
    categoria = servicio.crear(CategoriaCrear(nombre="Comida"))
    ServicioMovimientos(db, usuario).crear(nuevo_movimiento(categoria.id))

    with pytest.raises(ConflictoDeDatos):
        servicio.eliminar(categoria.id)
