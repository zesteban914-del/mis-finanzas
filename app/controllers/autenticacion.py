from typing import List

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.catalogos import OBJETIVOS_PERSONALES, SECTORES_NEGOCIO
from app.controllers.dependencias import obtener_usuario_actual, servicio
from app.database import obtener_db
from app.models import Usuario
from app.permisos import Funcion, Permiso
from app.schemas import (
    CambioContrasena,
    MiembroActualizar,
    MiembroCrear,
    MiembroRespuesta,
    OpcionesRegistro,
    PerfilActualizar,
    PlanInfo,
    RegistroUsuario,
    SesionRespuesta,
    UsuarioRespuesta,
)
from app.seguridad import crear_token
from app.services import ServicioAutenticacion, ServicioEquipo, ServicioPlanes

router = APIRouter(prefix="/auth", tags=["Autenticación y cuenta"])


def _sesion(usuario: Usuario) -> SesionRespuesta:
    return SesionRespuesta(
        access_token=crear_token(usuario.id),
        usuario=UsuarioRespuesta.model_validate(usuario),
    )


@router.get("/opciones-registro", response_model=OpcionesRegistro)
def opciones_registro():
    """Objetivos (cuenta personal) y sectores (cuenta de negocio) para el formulario."""
    return OpcionesRegistro(objetivos=OBJETIVOS_PERSONALES, sectores=SECTORES_NEGOCIO)


@router.post("/registro", response_model=SesionRespuesta, status_code=status.HTTP_201_CREATED)
def registrarse(datos: RegistroUsuario, db: Session = Depends(obtener_db)):
    """Crea una cuenta personal o de negocio y deja la sesión iniciada."""
    return _sesion(ServicioAutenticacion(db).registrar(datos))


@router.post("/login", response_model=SesionRespuesta)
def iniciar_sesion(
    formulario: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(obtener_db)
):
    """Formato estándar OAuth2: `username` es el correo y `password` la contraseña.
    También lo usa el botón *Authorize* de esta documentación."""
    usuario = ServicioAutenticacion(db).autenticar(formulario.username, formulario.password)
    return _sesion(usuario)


@router.get("/yo", response_model=UsuarioRespuesta)
def mi_cuenta(usuario: Usuario = Depends(obtener_usuario_actual)):
    """Datos de la cuenta, con sus permisos y funciones disponibles."""
    return usuario


@router.patch("/yo", response_model=UsuarioRespuesta)
def actualizar_perfil(
    datos: PerfilActualizar,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
):
    return ServicioAutenticacion(db).actualizar_perfil(usuario, datos)


@router.put("/yo/contrasena", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_contrasena(
    datos: CambioContrasena,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
):
    ServicioAutenticacion(db).cambiar_contrasena(usuario, datos)


# Planes ----------------------------------------------------------------------
planes = APIRouter(prefix="/planes", tags=["Planes"])


@planes.get("", response_model=List[PlanInfo])
def catalogo_de_planes(s: ServicioPlanes = Depends(servicio(ServicioPlanes))):
    """Planes disponibles para el tipo de cuenta del usuario, con precio y beneficios."""
    return s.catalogo()


@planes.post("/solicitar-pro", response_model=UsuarioRespuesta)
def solicitar_pro(s: ServicioPlanes = Depends(servicio(ServicioPlanes))):
    """Registra la solicitud; un administrador activa el plan (falta la pasarela de pago)."""
    return s.solicitar_pro()


# Equipo de un negocio -------------------------------------------------------------
equipo = APIRouter(prefix="/equipo", tags=["Equipo (negocios)"])
gestionar_equipo = servicio(ServicioEquipo, Permiso.GESTIONAR_EQUIPO, Funcion.EQUIPO)


@equipo.get("", response_model=List[MiembroRespuesta])
def listar_miembros(s: ServicioEquipo = Depends(gestionar_equipo)):
    return s.listar()


@equipo.post("", response_model=MiembroRespuesta, status_code=status.HTTP_201_CREATED)
def agregar_miembro(datos: MiembroCrear, s: ServicioEquipo = Depends(gestionar_equipo)):
    """Crea la cuenta de un empleado o contador con una contraseña inicial."""
    return s.agregar(datos)


@equipo.patch("/{miembro_id}", response_model=MiembroRespuesta)
def actualizar_miembro(
    miembro_id: int, datos: MiembroActualizar, s: ServicioEquipo = Depends(gestionar_equipo)
):
    return s.actualizar(miembro_id, datos)


@equipo.delete("/{miembro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_miembro(miembro_id: int, s: ServicioEquipo = Depends(gestionar_equipo)):
    s.eliminar(miembro_id)
