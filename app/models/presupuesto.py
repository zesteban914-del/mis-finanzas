from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class Presupuesto(Base):
    """Límite de gasto para un mes en formato AAAA-MM."""

    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    mes = Column(String(7), unique=True, nullable=False, index=True)
    limite = Column(Numeric(14, 2), nullable=False)
