from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PresupuestoCrear(BaseModel):
    mes: str = Field(examples=["2026-11"], description="Mes en formato AAAA-MM")
    limite: Decimal = Field(examples=[1500000])


class PresupuestoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mes: str
    limite: Decimal


class EstadoPresupuesto(BaseModel):
    """Comparación entre el límite del mes y lo realmente gastado."""

    mes: str
    limite: Decimal
    total_gastado: Decimal
    disponible: Decimal
    excedido: bool
