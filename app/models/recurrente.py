from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, Numeric, String

from app.database import Base
from app.models.movimiento import TipoMovimiento


class Recurrente(Base):
    """Movimiento que se repite cada mes (arriendo, salario, suscripciones).

    Cada vez que se abre la aplicación se registran los meses pendientes
    hasta hoy; `ultimo_mes_generado` evita registrarlos dos veces.
    """

    __tablename__ = "recurrentes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoMovimiento, name="tipo_movimiento"), nullable=False)
    monto = Column(Numeric(14, 2), nullable=False)
    descripcion = Column(String(255), nullable=False, default="")
    dia_del_mes = Column(Integer, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    caja_id = Column(Integer, ForeignKey("cajas.id"), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    mes_inicio = Column(String(7), nullable=False)  # AAAA-MM
    ultimo_mes_generado = Column(String(7), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
