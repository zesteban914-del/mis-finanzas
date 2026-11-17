"""Dependencias compartidas por los controladores (inyección de dependencias).

FastAPI las ejecuta antes de cada endpoint: leen el token del encabezado
`Authorization: Bearer <token>`, identifican al usuario, verifican que
tenga el permiso y la función necesarios, y entregan el servicio listo.

Uso en un endpoint:
    servicio: ServicioCategorias = Depends(servicio(ServicioCategorias, Permiso.GESTIONAR))
"""

from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.models import RolUsuario, Usuario
from app.permisos import Funcion, Permiso
from app.services import ServicioAdministracion, ServicioAutenticacion
from app.services.autorizacion import exigir_funcion, exigir_permiso
from app.services.excepciones import SinPermiso

# auto_error=False: si falta el token respondemos con nuestro propio mensaje.
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def obtener_usuario_actual(
    token: Optional[str] = Depends(esquema_oauth2), db: Session = Depends(obtener_db)
) -> Usuario:
    return ServicioAutenticacion(db).usuario_desde_token(token)


def servicio(clase, permiso: Optional[Permiso] = None, funcion: Optional[Funcion] = None):
    """Crea una dependencia que verifica permiso/función y construye el servicio."""

    def construir(
        db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)
    ):
        if funcion is not None:
            exigir_funcion(usuario, funcion)
        if permiso is not None:
            exigir_permiso(usuario, permiso)
        return clase(db, usuario)

    return construir


def requerir_administrador(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.ADMIN:
        raise SinPermiso("Esta sección es solo para administradores")
    return usuario


def servicio_administracion(
    db: Session = Depends(obtener_db),
    administrador: Usuario = Depends(requerir_administrador),
) -> ServicioAdministracion:
    return ServicioAdministracion(db, administrador)
