from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, UniqueConstraint

from app.database import Base


class Presupuesto(Base):
    """Límite de gasto de un usuario para un mes en formato AAAA-MM."""

    __tablename__ = "presupuestos"
    # Un solo presupuesto por mes para cada usuario.
    __table_args__ = (
        UniqueConstraint("usuario_id", "mes", name="uq_presupuesto_usuario_mes"),
    )

    id = Column(Integer, primary_key=True, index=True)
    mes = Column(String(7), nullable=False, index=True)
    limite = Column(Numeric(14, 2), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
