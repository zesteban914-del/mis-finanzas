"""Esquemas Pydantic: validan la entrada y dan forma a la salida de la API."""

from app.schemas.categoria import CategoriaCrear, CategoriaRespuesta
from app.schemas.movimiento import (
    MovimientoActualizar,
    MovimientoCreadoRespuesta,
    MovimientoCrear,
    MovimientoRespuesta,
)
from app.schemas.presupuesto import (
    EstadoPresupuesto,
    PresupuestoCrear,
    PresupuestoRespuesta,
)
from app.schemas.reporte import ResumenCategoria, ResumenMensual, SaldoRespuesta
from app.schemas.usuario import (
    CambioUsuarioAdmin,
    EstadisticasAdmin,
    RegistroUsuario,
    SesionRespuesta,
    UsuarioAdminRespuesta,
    UsuarioRespuesta,
)

__all__ = [
    "CategoriaCrear",
    "CategoriaRespuesta",
    "MovimientoCrear",
    "MovimientoActualizar",
    "MovimientoRespuesta",
    "MovimientoCreadoRespuesta",
    "PresupuestoCrear",
    "PresupuestoRespuesta",
    "EstadoPresupuesto",
    "SaldoRespuesta",
    "ResumenCategoria",
    "ResumenMensual",
    "RegistroUsuario",
    "UsuarioRespuesta",
    "SesionRespuesta",
    "UsuarioAdminRespuesta",
    "CambioUsuarioAdmin",
    "EstadisticasAdmin",
]
