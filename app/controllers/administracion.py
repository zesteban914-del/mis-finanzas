from typing import List

from fastapi import APIRouter, Depends

from app.controllers.dependencias import servicio_administracion
from app.schemas import (
    CambioUsuarioAdmin,
    EstadisticasAdmin,
    UsuarioAdminRespuesta,
    UsuarioRespuesta,
)
from app.services import ServicioAdministracion

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/usuarios", response_model=List[UsuarioAdminRespuesta])
def listar_usuarios(servicio: ServicioAdministracion = Depends(servicio_administracion)):
    """Cuentas registradas. No incluye montos ni movimientos (privacidad)."""
    return servicio.listar_usuarios()


@router.get("/estadisticas", response_model=EstadisticasAdmin)
def estadisticas(servicio: ServicioAdministracion = Depends(servicio_administracion)):
    return servicio.estadisticas()


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioRespuesta)
def actualizar_usuario(
    usuario_id: int,
    cambios: CambioUsuarioAdmin,
    servicio: ServicioAdministracion = Depends(servicio_administracion),
):
    """Activa o desactiva una cuenta, o cambia su rol."""
    return servicio.actualizar_usuario(usuario_id, cambios)
