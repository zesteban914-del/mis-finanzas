"""Capa de acceso a datos (patrón Repository)."""

from app.repositories.categoria_repositorio import RepositorioCategorias
from app.repositories.funciones_repositorio import (
    RepositorioCajas,
    RepositorioComprobantes,
    RepositorioDeudas,
    RepositorioMetas,
    RepositorioPresupuestosCategoria,
    RepositorioRecurrentes,
    RepositorioTransferencias,
)
from app.repositories.movimiento_repositorio import RepositorioMovimientos
from app.repositories.presupuesto_repositorio import RepositorioPresupuestos
from app.repositories.usuario_repositorio import RepositorioUsuarios

__all__ = [
    "RepositorioCajas",
    "RepositorioCategorias",
    "RepositorioComprobantes",
    "RepositorioDeudas",
    "RepositorioMetas",
    "RepositorioMovimientos",
    "RepositorioPresupuestos",
    "RepositorioPresupuestosCategoria",
    "RepositorioRecurrentes",
    "RepositorioTransferencias",
    "RepositorioUsuarios",
]
