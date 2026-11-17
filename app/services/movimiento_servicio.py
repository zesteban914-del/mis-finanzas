from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Movimiento, TipoMovimiento
from app.repositories import RepositorioCategorias, RepositorioMovimientos
from app.schemas import MovimientoActualizar, MovimientoCrear
from app.services.excepciones import ErrorDeValidacion, RecursoNoEncontrado
from app.services.presupuesto_servicio import ServicioPresupuestos


class ServicioMovimientos:
    """Reglas de negocio de los movimientos (ingresos y gastos) de un usuario."""

    def __init__(self, db: Session, usuario_id: int):
        self.repositorio = RepositorioMovimientos(db, usuario_id)
        self.repositorio_categorias = RepositorioCategorias(db, usuario_id)
        self.servicio_presupuestos = ServicioPresupuestos(db, usuario_id)

    def crear(self, datos: MovimientoCrear) -> Tuple[Movimiento, Optional[str]]:
        """Crea el movimiento y devuelve (movimiento, alerta de presupuesto)."""
        self._validar(datos.monto, datos.fecha, datos.categoria_id)
        movimiento = self.repositorio.crear(**datos.model_dump())
        return movimiento, self._alerta_presupuesto(movimiento)

    def obtener(self, movimiento_id: int) -> Movimiento:
        movimiento = self.repositorio.obtener_por_id(movimiento_id)
        if movimiento is None:
            raise RecursoNoEncontrado(
                f"El movimiento con id {movimiento_id} no existe"
            )
        return movimiento

    def listar(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        categoria_id: Optional[int] = None,
    ) -> List[Movimiento]:
        if (
            fecha_inicio is not None
            and fecha_fin is not None
            and fecha_inicio > fecha_fin
        ):
            raise ErrorDeValidacion(
                "La fecha inicial no puede ser mayor que la fecha final"
            )
        return self.repositorio.listar(fecha_inicio, fecha_fin, categoria_id)

    def actualizar(
        self, movimiento_id: int, datos: MovimientoActualizar
    ) -> Movimiento:
        movimiento = self.obtener(movimiento_id)
        cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
        self._validar(
            cambios.get("monto", movimiento.monto),
            cambios.get("fecha", movimiento.fecha),
            cambios.get("categoria_id", movimiento.categoria_id),
        )
        return self.repositorio.actualizar(movimiento, **cambios)

    def eliminar(self, movimiento_id: int) -> None:
        movimiento = self.obtener(movimiento_id)
        self.repositorio.eliminar(movimiento)

    def _validar(self, monto: Decimal, fecha: date, categoria_id: int) -> None:
        if monto is None or monto <= 0:
            raise ErrorDeValidacion("El monto debe ser mayor que 0")
        if fecha > date.today():
            raise ErrorDeValidacion("La fecha del movimiento no puede ser futura")
        if self.repositorio_categorias.obtener_por_id(categoria_id) is None:
            raise RecursoNoEncontrado(
                f"La categoría con id {categoria_id} no existe"
            )

    def _alerta_presupuesto(self, movimiento: Movimiento) -> Optional[str]:
        if movimiento.tipo != TipoMovimiento.GASTO:
            return None
        return self.servicio_presupuestos.alerta_si_excedido(
            movimiento.fecha.year, movimiento.fecha.month
        )
