from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Categoria(Base):
    """Categoría para clasificar los movimientos (ej. Comida, Transporte)."""

    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False, index=True)

    movimientos = relationship("Movimiento", back_populates="categoria")
