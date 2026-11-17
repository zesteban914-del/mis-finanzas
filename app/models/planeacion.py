"""Entidades de planeación: presupuesto por categoría, metas de ahorro y deudas."""

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint,
)

from app.database import Base
from app.models.usuario import ahora


class PresupuestoCategoria(Base):
    """Límite mensual de gasto para una categoría (aplica todos los meses)."""

    __tablename__ = "presupuestos_categoria"
    __table_args__ = (
        UniqueConstraint("usuario_id", "categoria_id", name="uq_presupuesto_categoria"),
    )

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(
        Integer, ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False
    )
    limite = Column(Numeric(14, 2), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)


class Meta(Base):
    """Meta de ahorro de una persona (ej. "Viaje": $2.000.000 para junio)."""

    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), nullable=False)
    monto_objetivo = Column(Numeric(14, 2), nullable=False)
    monto_ahorrado = Column(Numeric(14, 2), nullable=False, default=0)
    fecha_limite = Column(Date, nullable=True)
    creada_en = Column(DateTime(timezone=True), nullable=False, default=ahora)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)

    @property
    def porcentaje(self) -> int:
        return min(100, int(Decimal(self.monto_ahorrado) * 100 / Decimal(self.monto_objetivo)))

    @property
    def faltante(self) -> Decimal:
        return max(Decimal(0), Decimal(self.monto_objetivo) - Decimal(self.monto_ahorrado))

    @property
    def completada(self) -> bool:
        return Decimal(self.monto_ahorrado) >= Decimal(self.monto_objetivo)


class TipoDeuda(str, enum.Enum):
    POR_PAGAR = "POR_PAGAR"    # yo debo (deuda / cuenta por pagar a un proveedor)
    POR_COBRAR = "POR_COBRAR"  # me deben (préstamo / cuenta por cobrar a un cliente)


class EstadoDeuda(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    VENCIDA = "VENCIDA"
    PAGADA = "PAGADA"


class Deuda(Base):
    """Deuda o préstamo (persona) / cuenta por pagar o por cobrar (negocio)."""

    __tablename__ = "deudas"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoDeuda, name="tipo_deuda"), nullable=False)
    contraparte = Column(String(80), nullable=False)  # a quién / quién
    descripcion = Column(String(255), nullable=False, default="")
    monto_total = Column(Numeric(14, 2), nullable=False)
    monto_pagado = Column(Numeric(14, 2), nullable=False, default=0)
    fecha_vencimiento = Column(Date, nullable=True)
    creada_en = Column(DateTime(timezone=True), nullable=False, default=ahora)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)

    @property
    def pendiente(self) -> Decimal:
        return max(Decimal(0), Decimal(self.monto_total) - Decimal(self.monto_pagado))

    @property
    def estado(self) -> EstadoDeuda:
        if self.pendiente == 0:
            return EstadoDeuda.PAGADA
        if self.fecha_vencimiento and self.fecha_vencimiento < date.today():
            return EstadoDeuda.VENCIDA
        return EstadoDeuda.PENDIENTE
