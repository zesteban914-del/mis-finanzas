import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class TipoMovimiento(str, enum.Enum):
    INGRESO = "INGRESO"
    GASTO = "GASTO"


class Movimiento(Base):
    """Un ingreso o un gasto registrado por el usuario."""

    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoMovimiento, name="tipo_movimiento"), nullable=False)
    monto = Column(Numeric(14, 2), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    descripcion = Column(String(255), nullable=False, default="")
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)

    categoria = relationship("Categoria", back_populates="movimientos")
