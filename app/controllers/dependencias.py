"""Dependencias compartidas por los controladores (inyección de dependencias).

FastAPI las ejecuta antes de cada endpoint: leen el token del encabezado
`Authorization: Bearer <token>`, identifican al usuario y entregan el
servicio ya configurado para ese usuario.
"""

from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.models import RolUsuario, Usuario
from app.services import (
    ServicioAdministracion,
    ServicioAutenticacion,
    ServicioCategorias,
    ServicioMovimientos,
    ServicioPresupuestos,
    ServicioReportes,
)
from app.services.excepciones import SinPermiso

# auto_error=False: si falta el token respondemos con nuestro propio mensaje.
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def obtener_usuario_actual(
    token: Optional[str] = Depends(esquema_oauth2), db: Session = Depends(obtener_db)
) -> Usuario:
    return ServicioAutenticacion(db).usuario_desde_token(token)


def requerir_administrador(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    if usuario.rol != RolUsuario.ADMIN:
        raise SinPermiso("Esta sección es solo para administradores")
    return usuario


def servicio_categorias(
    db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)
) -> ServicioCategorias:
    return ServicioCategorias(db, usuario.id)


def servicio_movimientos(
    db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)
) -> ServicioMovimientos:
    return ServicioMovimientos(db, usuario.id)


def servicio_presupuestos(
    db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)
) -> ServicioPresupuestos:
    return ServicioPresupuestos(db, usuario.id)


def servicio_reportes(
    db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)
) -> ServicioReportes:
    return ServicioReportes(db, usuario.id)


def servicio_administracion(
    db: Session = Depends(obtener_db),
    administrador: Usuario = Depends(requerir_administrador),
) -> ServicioAdministracion:
    return ServicioAdministracion(db, administrador)
