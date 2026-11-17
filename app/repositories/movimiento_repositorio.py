from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Categoria, Movimiento, TipoMovimiento


def rango_del_mes(anio: int, mes: int) -> Tuple[date, date]:
    """Devuelve [primer día del mes, primer día del mes siguiente).

    Filtrar con >= inicio y < fin funciona igual en PostgreSQL y SQLite,
    a diferencia de funciones como date_trunc que son propias de Postgres.
    """
    inicio = date(anio, mes, 1)
    fin = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    return inicio, fin


class RepositorioMovimientos:
    """Operaciones de base de datos sobre la tabla de movimientos."""

    def __init__(self, db: Session):
        self.db = db

    def crear(self, **datos) -> Movimiento:
        movimiento = Movimiento(**datos)
        self.db.add(movimiento)
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def obtener_por_id(self, movimiento_id: int) -> Optional[Movimiento]:
        return self.db.get(Movimiento, movimiento_id)

    def listar(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        categoria_id: Optional[int] = None,
    ) -> List[Movimiento]:
        consulta = self.db.query(Movimiento)
        if fecha_inicio is not None:
            consulta = consulta.filter(Movimiento.fecha >= fecha_inicio)
        if fecha_fin is not None:
            consulta = consulta.filter(Movimiento.fecha <= fecha_fin)
        if categoria_id is not None:
            consulta = consulta.filter(Movimiento.categoria_id == categoria_id)
        return consulta.order_by(Movimiento.fecha.desc(), Movimiento.id.desc()).all()

    def actualizar(self, movimiento: Movimiento, **cambios) -> Movimiento:
        for campo, valor in cambios.items():
            setattr(movimiento, campo, valor)
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def eliminar(self, movimiento: Movimiento) -> None:
        self.db.delete(movimiento)
        self.db.commit()

    def contar_por_categoria(self, categoria_id: int) -> int:
        return (
            self.db.query(func.count(Movimiento.id))
            .filter(Movimiento.categoria_id == categoria_id)
            .scalar()
            or 0
        )

    def sumar_por_tipo(
        self,
        tipo: TipoMovimiento,
        anio: Optional[int] = None,
        mes: Optional[int] = None,
    ) -> Decimal:
        consulta = self.db.query(func.coalesce(func.sum(Movimiento.monto), 0)).filter(
            Movimiento.tipo == tipo
        )
        if anio is not None and mes is not None:
            inicio, fin = rango_del_mes(anio, mes)
            consulta = consulta.filter(
                Movimiento.fecha >= inicio, Movimiento.fecha < fin
            )
        return Decimal(str(consulta.scalar()))

    def totales_por_categoria(self, anio: int, mes: int):
        """Filas (categoria_id, nombre, tipo, total) del mes, agrupadas."""
        inicio, fin = rango_del_mes(anio, mes)
        return (
            self.db.query(
                Categoria.id,
                Categoria.nombre,
                Movimiento.tipo,
                func.sum(Movimiento.monto),
            )
            .join(Movimiento, Movimiento.categoria_id == Categoria.id)
            .filter(Movimiento.fecha >= inicio, Movimiento.fecha < fin)
            .group_by(Categoria.id, Categoria.nombre, Movimiento.tipo)
            .order_by(Categoria.nombre)
            .all()
        )
