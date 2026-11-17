from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.controllers.dependencias import obtener_usuario_actual
from app.database import obtener_db
from app.models import Usuario
from app.schemas import RegistroUsuario, SesionRespuesta, UsuarioRespuesta
from app.seguridad import crear_token
from app.services import ServicioAutenticacion

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _sesion(usuario: Usuario) -> SesionRespuesta:
    return SesionRespuesta(
        access_token=crear_token(usuario.id),
        usuario=UsuarioRespuesta.model_validate(usuario),
    )


@router.post(
    "/registro", response_model=SesionRespuesta, status_code=status.HTTP_201_CREATED
)
def registrarse(datos: RegistroUsuario, db: Session = Depends(obtener_db)):
    """Crea una cuenta nueva y deja la sesión iniciada."""
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
    """Datos de la cuenta con la que se inició sesión."""
    return usuario
