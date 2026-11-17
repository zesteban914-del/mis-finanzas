from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models import Plan, RolNegocio, RolUsuario, TipoCuenta


class RegistroUsuario(BaseModel):
    tipo_cuenta: TipoCuenta = TipoCuenta.PERSONAL
    nombre: str = Field(max_length=80, description="Tu nombre o el de tu negocio")
    email: str = Field(max_length=120, examples=["ana@correo.com"])
    contrasena: str = Field(max_length=128, examples=["MiClave2026"])
    acepta_terminos: bool = Field(
        default=False, description="Acepta términos y política de tratamiento de datos"
    )
    crear_categorias_iniciales: bool = True
    # Solo cuentas personales
    objetivo: Optional[str] = Field(default=None, max_length=40)
    # Solo cuentas de negocio
    sector: Optional[str] = Field(default=None, max_length=60)
    nit: Optional[str] = Field(default=None, max_length=20)
    responsable: Optional[str] = Field(default=None, max_length=80)


class PerfilActualizar(BaseModel):
    nombre: Optional[str] = Field(default=None, max_length=80)
    objetivo: Optional[str] = Field(default=None, max_length=40)
    sector: Optional[str] = Field(default=None, max_length=60)
    nit: Optional[str] = Field(default=None, max_length=20)
    responsable: Optional[str] = Field(default=None, max_length=80)


class CambioContrasena(BaseModel):
    actual: str = Field(max_length=128)
    nueva: str = Field(max_length=128)


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    rol: RolUsuario
    activo: bool
    creado_en: datetime
    tipo_cuenta: TipoCuenta
    plan: Plan = Field(validation_alias=AliasChoices("plan_efectivo", "plan"))
    solicito_pro_en: Optional[datetime] = None
    objetivo: Optional[str] = None
    sector: Optional[str] = None
    nit: Optional[str] = None
    responsable: Optional[str] = None
    negocio_id: Optional[int] = None
    rol_negocio: Optional[RolNegocio] = None
    nombre_negocio: Optional[str] = None
    permisos: List[str] = []
    funciones: List[str] = []
    limites: dict = {}


class SesionRespuesta(BaseModel):
    """Formato estándar OAuth2 (access_token, token_type) más los datos del usuario."""

    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioRespuesta


class OpcionesRegistro(BaseModel):
    objetivos: dict
    sectores: dict


class UsuarioAdminRespuesta(UsuarioRespuesta):
    """Lo que ve el administrador: datos de la cuenta, nunca montos ni movimientos."""

    movimientos_registrados: int


class CambioUsuarioAdmin(BaseModel):
    activo: Optional[bool] = None
    rol: Optional[RolUsuario] = None
    plan: Optional[Plan] = None


class EstadisticasAdmin(BaseModel):
    total_usuarios: int
    usuarios_activos: int
    administradores: int
    movimientos_registrados: int
    cuentas_personales: int
    cuentas_negocio: int
    cuentas_pro: int
    solicitudes_pro: int
    ingreso_mensual_estimado: int


class PlanInfo(BaseModel):
    plan: Plan
    precio_mensual: int
    beneficios: List[str]
    actual: bool


class MiembroCrear(BaseModel):
    nombre: str = Field(max_length=80)
    email: str = Field(max_length=120)
    contrasena: str = Field(max_length=128, description="Contraseña inicial del miembro")
    rol_negocio: RolNegocio


class MiembroActualizar(BaseModel):
    rol_negocio: Optional[RolNegocio] = None
    activo: Optional[bool] = None


class MiembroRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    rol_negocio: RolNegocio
    activo: bool
    creado_en: datetime
