"""Esquemas Pydantic: validan la entrada y dan forma a la salida de la API."""

from app.schemas.categoria import CategoriaCrear, CategoriaRespuesta
from app.schemas.funciones import (
    Aporte,
    CajaActualizar,
    CajaCrear,
    CajaRespuesta,
    DeudaActualizar,
    DeudaCrear,
    DeudaRespuesta,
    EstadoPresupuestoCategoria,
    GeneracionRespuesta,
    MetaActualizar,
    MetaCrear,
    MetaRespuesta,
    PresupuestoCategoriaDefinir,
    RecurrenteActualizar,
    RecurrenteCrear,
    RecurrenteRespuesta,
    TransferenciaCrear,
    TransferenciaRespuesta,
)
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
    CambioContrasena,
    CambioUsuarioAdmin,
    EstadisticasAdmin,
    MiembroActualizar,
    MiembroCrear,
    MiembroRespuesta,
    OpcionesRegistro,
    PerfilActualizar,
    PlanInfo,
    RegistroUsuario,
    SesionRespuesta,
    UsuarioAdminRespuesta,
    UsuarioRespuesta,
)
