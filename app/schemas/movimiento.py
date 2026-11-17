from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import TipoMovimiento


class MovimientoCrear(BaseModel):
    tipo: TipoMovimiento
    monto: Decimal = Field(examples=[50000])
    fecha: date
    descripcion: str = Field(default="", max_length=255)
    categoria_id: int
    caja_id: Optional[int] = Field(default=None, description="Solo cuentas de negocio")


class MovimientoActualizar(BaseModel):
    """Todos los campos son opcionales: solo se actualiza lo que se envía.
    Enviar caja_id = null quita la caja del movimiento."""

    tipo: Optional[TipoMovimiento] = None
    monto: Optional[Decimal] = None
    fecha: Optional[date] = None
    descripcion: Optional[str] = Field(default=None, max_length=255)
    categoria_id: Optional[int] = None
    caja_id: Optional[int] = None


class MovimientoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoMovimiento
    monto: Decimal
    fecha: date
    descripcion: str
    categoria_id: int
    caja_id: Optional[int] = None
    recurrente_id: Optional[int] = None
    registrado_por_nombre: Optional[str] = None
    tiene_comprobante: bool = False


class MovimientoCreadoRespuesta(BaseModel):
    """Respuesta al crear un movimiento; incluye las alertas de presupuesto si aplican."""

    movimiento: MovimientoRespuesta
    alerta_presupuesto: Optional[str] = None
    alertas: List[str] = []
