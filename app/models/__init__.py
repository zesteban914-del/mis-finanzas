"""Entidades del dominio (tablas de la base de datos)."""

from app.models.categoria import Categoria
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.presupuesto import Presupuesto

__all__ = ["Categoria", "Movimiento", "TipoMovimiento", "Presupuesto"]
