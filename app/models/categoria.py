from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Categoria(Base):
    """Categoría para clasificar los movimientos (ej. Comida, Transporte)."""

    __tablename__ = "categorias"
    # El nombre es único por usuario: dos usuarios pueden tener "Comida".
    __table_args__ = (
        UniqueConstraint("usuario_id", "nombre", name="uq_categoria_usuario_nombre"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)

    movimientos = relationship("Movimiento", back_populates="categoria")
