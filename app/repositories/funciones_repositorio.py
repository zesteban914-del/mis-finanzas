"""Repositorios de las funciones adicionales. Heredan el filtro por titular."""

from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import func, or_

from app.models import (
    Caja,
    Comprobante,
    Deuda,
    Meta,
    PresupuestoCategoria,
    Recurrente,
    Transferencia,
)
from app.repositories.base import RepositorioDelTitular


class RepositorioRecurrentes(RepositorioDelTitular):
    modelo = Recurrente

    def listar_activos(self) -> List[Recurrente]:
        return self._consulta().filter(Recurrente.activo.is_(True)).all()

    def contar_por_categoria(self, categoria_id: int) -> int:
        return self._consulta().filter(Recurrente.categoria_id == categoria_id).count()


class RepositorioPresupuestosCategoria(RepositorioDelTitular):
    modelo = PresupuestoCategoria

    def obtener_por_categoria(self, categoria_id: int) -> Optional[PresupuestoCategoria]:
        return self._consulta().filter(PresupuestoCategoria.categoria_id == categoria_id).first()


class RepositorioMetas(RepositorioDelTitular):
    modelo = Meta


class RepositorioDeudas(RepositorioDelTitular):
    modelo = Deuda


class RepositorioCajas(RepositorioDelTitular):
    modelo = Caja

    def obtener_por_nombre(self, nombre: str) -> Optional[Caja]:
        return self._consulta().filter(Caja.nombre == nombre).first()


class RepositorioTransferencias(RepositorioDelTitular):
    modelo = Transferencia

    def listar(self) -> List[Transferencia]:
        return super().listar(Transferencia.fecha.desc(), Transferencia.id.desc())

    def contar_por_caja(self, caja_id: int) -> int:
        return (
            self._consulta()
            .filter(or_(Transferencia.origen_id == caja_id, Transferencia.destino_id == caja_id))
            .count()
        )

    def entradas_y_salidas(self) -> Dict[int, Decimal]:
        """{caja_id: entradas - salidas} de todas las transferencias."""
        neto: Dict[int, Decimal] = {}
        for columna, signo in ((Transferencia.destino_id, 1), (Transferencia.origen_id, -1)):
            filas = (
                self.db.query(columna, func.sum(Transferencia.monto))
                .filter(Transferencia.usuario_id == self.titular_id)
                .group_by(columna)
                .all()
            )
            for caja_id, total in filas:
                neto[caja_id] = neto.get(caja_id, Decimal(0)) + signo * Decimal(str(total))
        return neto


class RepositorioComprobantes:
    """Los comprobantes cuelgan de un movimiento: la propiedad se verifica
    obteniendo primero el movimiento con el repositorio de movimientos."""

    def __init__(self, db):
        self.db = db

    def guardar(self, movimiento, nombre: str, tipo: str, contenido: bytes) -> Comprobante:
        if movimiento.comprobante is not None:
            self.db.delete(movimiento.comprobante)
            self.db.flush()
        comprobante = Comprobante(
            movimiento_id=movimiento.id,
            nombre_archivo=nombre,
            tipo_contenido=tipo,
            tamano=len(contenido),
            contenido=contenido,
        )
        self.db.add(comprobante)
        self.db.commit()
        self.db.refresh(movimiento)
        return comprobante

    def eliminar(self, comprobante: Comprobante) -> None:
        self.db.delete(comprobante)
        self.db.commit()
