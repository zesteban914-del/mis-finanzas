"""Capa de acceso a datos (patrón Repository)."""

from app.repositories.categoria_repositorio import RepositorioCategorias
from app.repositories.movimiento_repositorio import RepositorioMovimientos
from app.repositories.presupuesto_repositorio import RepositorioPresupuestos

__all__ = [
    "RepositorioCategorias",
    "RepositorioMovimientos",
    "RepositorioPresupuestos",
]
