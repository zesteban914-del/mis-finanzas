from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func

from app.models import Categoria, Movimiento, TipoMovimiento
from app.repositories.base import RepositorioDelTitular


def rango_del_mes(anio: int, mes: int) -> Tuple[date, date]:
    """Devuelve [primer día del mes, primer día del mes siguiente).

    Filtrar con >= inicio y < fin funciona igual en PostgreSQL y SQLite,
    a diferencia de funciones como date_trunc que son propias de Postgres.
    """
    inicio = date(anio, mes, 1)
    fin = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    return inicio, fin


class RepositorioMovimientos(RepositorioDelTitular):
    """Movimientos de un titular."""

    modelo = Movimiento

    def _consulta_columnas(self, *columnas):
        return self.db.query(*columnas).filter(Movimiento.usuario_id == self.titular_id)

    def listar(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        categoria_id: Optional[int] = None,
        caja_id: Optional[int] = None,
    ) -> List[Movimiento]:
        consulta = self._consulta()
        if fecha_inicio is not None:
            consulta = consulta.filter(Movimiento.fecha >= fecha_inicio)
        if fecha_fin is not None:
            consulta = consulta.filter(Movimiento.fecha <= fecha_fin)
        if categoria_id is not None:
            consulta = consulta.filter(Movimiento.categoria_id == categoria_id)
        if caja_id is not None:
            consulta = consulta.filter(Movimiento.caja_id == caja_id)
        return consulta.order_by(Movimiento.fecha.desc(), Movimiento.id.desc()).all()

    def contar_por_categoria(self, categoria_id: int) -> int:
        return (
            self._consulta_columnas(func.count(Movimiento.id))
            .filter(Movimiento.categoria_id == categoria_id)
            .scalar()
            or 0
        )

    def contar_por_caja(self, caja_id: int) -> int:
        return (
            self._consulta_columnas(func.count(Movimiento.id))
            .filter(Movimiento.caja_id == caja_id)
            .scalar()
            or 0
        )

    def sumar_por_tipo(
        self,
        tipo: TipoMovimiento,
        anio: Optional[int] = None,
        mes: Optional[int] = None,
        categoria_id: Optional[int] = None,
    ) -> Decimal:
        consulta = self._consulta_columnas(
            func.coalesce(func.sum(Movimiento.monto), 0)
        ).filter(Movimiento.tipo == tipo)
        if anio is not None and mes is not None:
            inicio, fin = rango_del_mes(anio, mes)
            consulta = consulta.filter(Movimiento.fecha >= inicio, Movimiento.fecha < fin)
        if categoria_id is not None:
            consulta = consulta.filter(Movimiento.categoria_id == categoria_id)
        return Decimal(str(consulta.scalar()))

    def totales_por_categoria(self, anio: int, mes: int):
        """Filas (categoria_id, nombre, tipo, total) del mes, agrupadas."""
        inicio, fin = rango_del_mes(anio, mes)
        return (
            self.db.query(Categoria.id, Categoria.nombre, Movimiento.tipo, func.sum(Movimiento.monto))
            .select_from(Movimiento)
            .join(Categoria, Movimiento.categoria_id == Categoria.id)
            .filter(Movimiento.usuario_id == self.titular_id)
            .filter(Movimiento.fecha >= inicio, Movimiento.fecha < fin)
            .group_by(Categoria.id, Categoria.nombre, Movimiento.tipo)
            .order_by(Categoria.nombre)
            .all()
        )

    def gastos_por_categoria(self, anio: int, mes: int) -> Dict[int, Decimal]:
        inicio, fin = rango_del_mes(anio, mes)
        filas = (
            self._consulta_columnas(Movimiento.categoria_id, func.sum(Movimiento.monto))
            .filter(Movimiento.tipo == TipoMovimiento.GASTO)
            .filter(Movimiento.fecha >= inicio, Movimiento.fecha < fin)
            .group_by(Movimiento.categoria_id)
            .all()
        )
        return {categoria_id: Decimal(str(total)) for categoria_id, total in filas}

    def totales_por_caja(self) -> Dict[Tuple[int, TipoMovimiento], Decimal]:
        """{(caja_id, tipo): total} para calcular el saldo de cada caja."""
        filas = (
            self._consulta_columnas(Movimiento.caja_id, Movimiento.tipo, func.sum(Movimiento.monto))
            .filter(Movimiento.caja_id.isnot(None))
            .group_by(Movimiento.caja_id, Movimiento.tipo)
            .all()
        )
        return {(caja_id, tipo): Decimal(str(total)) for caja_id, tipo, total in filas}

    def quitar_autor(self, autor_id: int) -> None:
        """Al eliminar a un miembro del equipo, sus movimientos quedan sin autor."""
        self._consulta().filter(Movimiento.registrado_por_id == autor_id).update(
            {Movimiento.registrado_por_id: None}, synchronize_session=False
        )
        self.db.commit()
