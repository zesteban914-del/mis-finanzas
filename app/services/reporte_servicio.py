from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import TipoMovimiento
from app.repositories import RepositorioMovimientos
from app.schemas import ResumenCategoria, ResumenMensual, SaldoRespuesta
from app.services.validaciones import validar_mes


class ServicioReportes:
    """Cálculos de saldo y resumen mensual de un usuario."""

    def __init__(self, db: Session, usuario_id: int):
        self.repositorio_movimientos = RepositorioMovimientos(db, usuario_id)

    def saldo(self) -> SaldoRespuesta:
        """Saldo = suma de ingresos - suma de gastos."""
        total_ingresos = self.repositorio_movimientos.sumar_por_tipo(
            TipoMovimiento.INGRESO
        )
        total_gastos = self.repositorio_movimientos.sumar_por_tipo(
            TipoMovimiento.GASTO
        )
        return SaldoRespuesta(
            total_ingresos=total_ingresos,
            total_gastos=total_gastos,
            saldo=total_ingresos - total_gastos,
        )

    def resumen_mensual(self, mes: str) -> ResumenMensual:
        """Totales del mes agrupados por categoría."""
        anio, numero_mes = validar_mes(mes)
        filas = self.repositorio_movimientos.totales_por_categoria(anio, numero_mes)

        por_categoria = {}
        for categoria_id, nombre, tipo, total in filas:
            resumen = por_categoria.setdefault(
                categoria_id,
                {
                    "categoria_id": categoria_id,
                    "categoria": nombre,
                    "total_ingresos": Decimal("0"),
                    "total_gastos": Decimal("0"),
                },
            )
            total = Decimal(str(total))
            if tipo == TipoMovimiento.INGRESO:
                resumen["total_ingresos"] += total
            else:
                resumen["total_gastos"] += total

        categorias = [ResumenCategoria(**datos) for datos in por_categoria.values()]
        total_ingresos = sum(
            (c.total_ingresos for c in categorias), Decimal("0")
        )
        total_gastos = sum((c.total_gastos for c in categorias), Decimal("0"))
        return ResumenMensual(
            mes=mes,
            categorias=categorias,
            total_ingresos=total_ingresos,
            total_gastos=total_gastos,
            balance=total_ingresos - total_gastos,
        )
