import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class RolUsuario(str, enum.Enum):
    """Rol en la PLATAFORMA: quién administra las cuentas."""

    USUARIO = "USUARIO"
    ADMIN = "ADMIN"


class TipoCuenta(str, enum.Enum):
    """Para qué se usa la cuenta: decide qué datos se piden y qué funciones hay."""

    PERSONAL = "PERSONAL"
    NEGOCIO = "NEGOCIO"


class Plan(str, enum.Enum):
    GRATIS = "GRATIS"
    PRO = "PRO"


class RolNegocio(str, enum.Enum):
    """Rol dentro de un NEGOCIO: el propietario invita empleados y contadores."""

    PROPIETARIO = "PROPIETARIO"
    EMPLEADO = "EMPLEADO"
    CONTADOR = "CONTADOR"


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    """Persona o negocio que usa la aplicación."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), nullable=False)  # persona o nombre del negocio
    email = Column(String(120), unique=True, nullable=False, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(
        Enum(RolUsuario, name="rol_usuario"), nullable=False, default=RolUsuario.USUARIO
    )
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, default=ahora)

    tipo_cuenta = Column(
        Enum(TipoCuenta, name="tipo_cuenta"),
        nullable=False,
        default=TipoCuenta.PERSONAL,
        server_default=TipoCuenta.PERSONAL.value,
    )
    plan = Column(
        Enum(Plan, name="plan_suscripcion"),
        nullable=False,
        default=Plan.GRATIS,
        server_default=Plan.GRATIS.value,
    )
    solicito_pro_en = Column(DateTime(timezone=True), nullable=True)
    acepto_terminos_en = Column(DateTime(timezone=True), nullable=True)

    # Datos de una cuenta personal
    objetivo = Column(String(40), nullable=True)
    # Datos de una cuenta de negocio
    sector = Column(String(60), nullable=True)
    nit = Column(String(20), nullable=True)
    responsable = Column(String(80), nullable=True)

    # Miembros de un equipo: apuntan a la cuenta del negocio al que pertenecen.
    negocio_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    rol_negocio = Column(Enum(RolNegocio, name="rol_negocio"), nullable=True)

    negocio = relationship("Usuario", remote_side=[id], lazy="joined")

    @property
    def titular_id(self) -> int:
        """Id del dueño de los datos: el propio usuario o el negocio al que pertenece."""
        return self.negocio_id or self.id

    @property
    def plan_efectivo(self) -> Plan:
        """Los miembros de un equipo usan el plan del negocio."""
        return self.negocio.plan if self.negocio_id else self.plan

    @property
    def nombre_negocio(self):
        if self.negocio_id:
            return self.negocio.nombre
        return self.nombre if self.tipo_cuenta == TipoCuenta.NEGOCIO else None

    @property
    def permisos(self) -> list:
        from app.permisos import permisos_de

        return sorted(p.value for p in permisos_de(self))

    @property
    def limites(self) -> dict:
        from app.planes import LIMITES

        return LIMITES[self.plan_efectivo]

    @property
    def funciones(self) -> list:
        from app.permisos import funciones_de

        return sorted(f.value for f in funciones_de(self))
