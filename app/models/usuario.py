import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String

from app.database import Base


class RolUsuario(str, enum.Enum):
    USUARIO = "USUARIO"
    ADMIN = "ADMIN"


class Usuario(Base):
    """Persona o negocio que usa la aplicación. Cada uno ve solo sus datos."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(
        Enum(RolUsuario, name="rol_usuario"), nullable=False, default=RolUsuario.USUARIO
    )
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
