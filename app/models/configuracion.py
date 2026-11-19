from sqlalchemy import Column, String

from app.database import Base


class Configuracion(Base):
    """Valores internos de la aplicación (por ejemplo, la clave que firma las sesiones)."""

    __tablename__ = "configuracion"

    clave = Column(String(60), primary_key=True)
    valor = Column(String(255), nullable=False)
