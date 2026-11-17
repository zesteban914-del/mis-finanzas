import enum

from sqlalchemy import (
    Column, Date, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint,
)

from app.database import Base


class TipoCaja(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    BANCO = "BANCO"
    BILLETERA = "BILLETERA"  # Nequi, Daviplata...


class Caja(Base):
    """Dónde está el dinero de un negocio: caja de efectivo, banco o billetera."""

    __tablename__ = "cajas"
    __table_args__ = (UniqueConstraint("usuario_id", "nombre", name="uq_caja_usuario_nombre"),)

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(60), nullable=False)
    tipo = Column(Enum(TipoCaja, name="tipo_caja"), nullable=False)
    saldo_inicial = Column(Numeric(14, 2), nullable=False, default=0)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)


class Transferencia(Base):
    """Mover dinero entre cajas. No es ingreso ni gasto: no cambia el saldo total."""

    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True, index=True)
    origen_id = Column(Integer, ForeignKey("cajas.id"), nullable=False)
    destino_id = Column(Integer, ForeignKey("cajas.id"), nullable=False)
    monto = Column(Numeric(14, 2), nullable=False)
    fecha = Column(Date, nullable=False)
    descripcion = Column(String(255), nullable=False, default="")
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
