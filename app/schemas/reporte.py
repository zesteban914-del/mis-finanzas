from decimal import Decimal
from typing import List

from pydantic import BaseModel


class SaldoRespuesta(BaseModel):
    """Saldo global: total de ingresos menos total de gastos."""

    total_ingresos: Decimal
    total_gastos: Decimal
    saldo: Decimal


class ResumenCategoria(BaseModel):
    categoria_id: int
    categoria: str
    total_ingresos: Decimal
    total_gastos: Decimal


class ResumenMensual(BaseModel):
    """Totales de un mes agrupados por categoría."""

    mes: str
    categorias: List[ResumenCategoria]
    total_ingresos: Decimal
    total_gastos: Decimal
    balance: Decimal
