import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class TipoMovimiento(str, enum.Enum):
    INGRESO = "INGRESO"
    GASTO = "GASTO"


class Movimiento(Base):
    """Un ingreso o un gasto registrado en una cuenta."""

    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoMovimiento, name="tipo_movimiento"), nullable=False)
    monto = Column(Numeric(14, 2), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    descripcion = Column(String(255), nullable=False, default="")
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    # Opcionales: caja del negocio, quién lo registró y si salió de un recurrente.
    caja_id = Column(Integer, ForeignKey("cajas.id"), nullable=True, index=True)
    registrado_por_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    recurrente_id = Column(
        Integer, ForeignKey("recurrentes.id", ondelete="SET NULL"), nullable=True
    )

    categoria = relationship("Categoria", back_populates="movimientos")
    registrado_por = relationship(
        "Usuario", foreign_keys=[registrado_por_id], lazy="selectin"
    )
    comprobante = relationship(
        "Comprobante",
        uselist=False,
        lazy="selectin",
        back_populates="movimiento",
        cascade="all, delete-orphan",
    )

    @property
    def tiene_comprobante(self) -> bool:
        return self.comprobante is not None

    @property
    def registrado_por_nombre(self):
        return self.registrado_por.nombre if self.registrado_por else None
