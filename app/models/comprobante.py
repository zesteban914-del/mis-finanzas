from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import deferred, relationship

from app.database import Base
from app.models.usuario import ahora


class Comprobante(Base):
    """Foto o PDF de la factura/recibo de un movimiento (uno por movimiento)."""

    __tablename__ = "comprobantes"

    id = Column(Integer, primary_key=True, index=True)
    movimiento_id = Column(
        Integer, ForeignKey("movimientos.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    nombre_archivo = Column(String(150), nullable=False)
    tipo_contenido = Column(String(60), nullable=False)
    tamano = Column(Integer, nullable=False)
    # deferred: el archivo solo se lee de la base cuando se descarga.
    contenido = deferred(Column(LargeBinary, nullable=False))
    subido_en = Column(DateTime(timezone=True), nullable=False, default=ahora)

    movimiento = relationship("Movimiento", back_populates="comprobante")
