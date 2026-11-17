from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import RolUsuario


class RegistroUsuario(BaseModel):
    nombre: str = Field(max_length=80, examples=["Ana Martínez"])
    email: str = Field(max_length=120, examples=["ana@correo.com"])
    contrasena: str = Field(max_length=128, examples=["MiClave2026"])
    crear_categorias_iniciales: bool = Field(
        default=True,
        description="Crea categorías sugeridas (Salario, Comida, Transporte...)",
    )


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    rol: RolUsuario
    activo: bool
    creado_en: datetime


class SesionRespuesta(BaseModel):
    """Formato estándar OAuth2 (access_token, token_type) más los datos del usuario."""

    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioRespuesta


class UsuarioAdminRespuesta(UsuarioRespuesta):
    """Lo que ve el administrador: datos de la cuenta, nunca montos ni movimientos."""

    movimientos_registrados: int


class CambioUsuarioAdmin(BaseModel):
    activo: Optional[bool] = None
    rol: Optional[RolUsuario] = None


class EstadisticasAdmin(BaseModel):
    total_usuarios: int
    usuarios_activos: int
    administradores: int
    movimientos_registrados: int
