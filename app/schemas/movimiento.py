from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import TipoMovimiento


class MovimientoCrear(BaseModel):
    tipo: TipoMovimiento
    monto: Decimal = Field(examples=[50000])
    fecha: date
    descripcion: str = Field(default="", max_length=255)
    categoria_id: int


class MovimientoActualizar(BaseModel):
    """Todos los campos son opcionales: solo se actualiza lo que se envía."""

    tipo: Optional[TipoMovimiento] = None
    monto: Optional[Decimal] = None
    fecha: Optional[date] = None
    descripcion: Optional[str] = Field(default=None, max_length=255)
    categoria_id: Optional[int] = None


class MovimientoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoMovimiento
    monto: Decimal
    fecha: date
    descripcion: str
    categoria_id: int


class MovimientoCreadoRespuesta(BaseModel):
    """Respuesta al crear un movimiento; incluye la alerta de presupuesto si aplica."""

    movimiento: MovimientoRespuesta
    alerta_presupuesto: Optional[str] = None
