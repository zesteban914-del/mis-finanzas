"""Esquemas de las funciones adicionales: recurrentes, presupuesto por
categoría, metas, deudas, cajas y transferencias."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoDeuda, TipoCaja, TipoDeuda, TipoMovimiento


# Movimientos recurrentes ---------------------------------------------------
class RecurrenteCrear(BaseModel):
    tipo: TipoMovimiento
    monto: Decimal
    descripcion: str = Field(default="", max_length=255)
    dia_del_mes: int = Field(description="Día en que se registra (1 a 28)")
    categoria_id: int
    caja_id: Optional[int] = None
    mes_inicio: Optional[str] = Field(default=None, description="AAAA-MM; por defecto el mes actual")


class RecurrenteActualizar(BaseModel):
    monto: Optional[Decimal] = None
    descripcion: Optional[str] = Field(default=None, max_length=255)
    dia_del_mes: Optional[int] = None
    categoria_id: Optional[int] = None
    activo: Optional[bool] = None


class RecurrenteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoMovimiento
    monto: Decimal
    descripcion: str
    dia_del_mes: int
    categoria_id: int
    caja_id: Optional[int]
    activo: bool
    mes_inicio: str
    ultimo_mes_generado: Optional[str]


class GeneracionRespuesta(BaseModel):
    movimientos_creados: int


# Presupuesto por categoría -------------------------------------------------
class PresupuestoCategoriaDefinir(BaseModel):
    limite: Decimal


class EstadoPresupuestoCategoria(BaseModel):
    categoria_id: int
    categoria: str
    limite: Decimal
    gastado: Decimal
    disponible: Decimal
    porcentaje: int
    excedido: bool


# Metas de ahorro -----------------------------------------------------------
class MetaCrear(BaseModel):
    nombre: str = Field(max_length=80)
    monto_objetivo: Decimal
    fecha_limite: Optional[date] = None


class MetaActualizar(BaseModel):
    nombre: Optional[str] = Field(default=None, max_length=80)
    monto_objetivo: Optional[Decimal] = None
    fecha_limite: Optional[date] = None


class Aporte(BaseModel):
    monto: Decimal


class MetaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    monto_objetivo: Decimal
    monto_ahorrado: Decimal
    fecha_limite: Optional[date]
    porcentaje: int
    faltante: Decimal
    completada: bool


# Deudas y préstamos / cuentas por pagar y cobrar ---------------------------
class DeudaCrear(BaseModel):
    tipo: TipoDeuda
    contraparte: str = Field(max_length=80, description="Persona, cliente o proveedor")
    monto_total: Decimal
    descripcion: str = Field(default="", max_length=255)
    fecha_vencimiento: Optional[date] = None


class DeudaActualizar(BaseModel):
    contraparte: Optional[str] = Field(default=None, max_length=80)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    monto_total: Optional[Decimal] = None
    fecha_vencimiento: Optional[date] = None


class DeudaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoDeuda
    contraparte: str
    descripcion: str
    monto_total: Decimal
    monto_pagado: Decimal
    pendiente: Decimal
    fecha_vencimiento: Optional[date]
    estado: EstadoDeuda


# Cajas y transferencias ----------------------------------------------------
class CajaCrear(BaseModel):
    nombre: str = Field(max_length=60, examples=["Caja principal", "Bancolombia", "Nequi"])
    tipo: TipoCaja
    saldo_inicial: Decimal = Decimal(0)


class CajaActualizar(BaseModel):
    nombre: Optional[str] = Field(default=None, max_length=60)
    tipo: Optional[TipoCaja] = None
    saldo_inicial: Optional[Decimal] = None


class CajaRespuesta(BaseModel):
    id: int
    nombre: str
    tipo: TipoCaja
    saldo_inicial: Decimal
    saldo_actual: Decimal


class TransferenciaCrear(BaseModel):
    origen_id: int
    destino_id: int
    monto: Decimal
    fecha: date
    descripcion: str = Field(default="", max_length=255)


class TransferenciaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origen_id: int
    destino_id: int
    monto: Decimal
    fecha: date
    descripcion: str
