from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Movimiento, TipoMovimiento, Usuario
from app.repositories import RepositorioCajas, RepositorioCategorias, RepositorioMovimientos
from app.schemas import MovimientoActualizar, MovimientoCrear
from app.services.excepciones import ErrorDeValidacion, RecursoNoEncontrado
from app.services.presupuesto_servicio import ServicioPresupuestos
from app.services.presupuesto_categoria_servicio import ServicioPresupuestosCategoria


class ServicioMovimientos:
    """Reglas de negocio de los movimientos (ingresos y gastos)."""

    def __init__(self, db: Session, usuario: Usuario):
        self.usuario = usuario
        self.repositorio = RepositorioMovimientos(db, usuario.titular_id)
        self.repositorio_categorias = RepositorioCategorias(db, usuario.titular_id)
        self.repositorio_cajas = RepositorioCajas(db, usuario.titular_id)
        self.servicio_presupuestos = ServicioPresupuestos(db, usuario)
        self.servicio_presupuestos_categoria = ServicioPresupuestosCategoria(db, usuario)

    def crear(self, datos: MovimientoCrear) -> Tuple[Movimiento, List[str]]:
        """Crea el movimiento y devuelve (movimiento, alertas de presupuesto)."""
        self._validar(datos.monto, datos.fecha, datos.categoria_id, datos.caja_id)
        movimiento = self.repositorio.crear(
            **datos.model_dump(), registrado_por_id=self.usuario.id
        )
        return movimiento, self._alertas(movimiento)

    def obtener(self, movimiento_id: int) -> Movimiento:
        movimiento = self.repositorio.obtener_por_id(movimiento_id)
        if movimiento is None:
            raise RecursoNoEncontrado(f"El movimiento con id {movimiento_id} no existe")
        return movimiento

    def listar(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        categoria_id: Optional[int] = None,
        caja_id: Optional[int] = None,
    ) -> List[Movimiento]:
        if fecha_inicio is not None and fecha_fin is not None and fecha_inicio > fecha_fin:
            raise ErrorDeValidacion("La fecha inicial no puede ser mayor que la fecha final")
        return self.repositorio.listar(fecha_inicio, fecha_fin, categoria_id, caja_id)

    def actualizar(self, movimiento_id: int, datos: MovimientoActualizar) -> Movimiento:
        movimiento = self.obtener(movimiento_id)
        cambios = datos.model_dump(exclude_unset=True)
        # null significa "no cambiar", excepto en caja_id, donde significa "quitar la caja".
        cambios = {k: v for k, v in cambios.items() if v is not None or k == "caja_id"}
        self._validar(
            cambios.get("monto", movimiento.monto),
            cambios.get("fecha", movimiento.fecha),
            cambios.get("categoria_id", movimiento.categoria_id),
            cambios.get("caja_id", movimiento.caja_id),
        )
        return self.repositorio.actualizar(movimiento, **cambios)

    def eliminar(self, movimiento_id: int) -> None:
        self.repositorio.eliminar(self.obtener(movimiento_id))

    def _validar(self, monto: Decimal, fecha: date, categoria_id: int, caja_id: Optional[int]) -> None:
        if monto is None or monto <= 0:
            raise ErrorDeValidacion("El monto debe ser mayor que 0")
        if fecha > date.today():
            raise ErrorDeValidacion("La fecha del movimiento no puede ser futura")
        if self.repositorio_categorias.obtener_por_id(categoria_id) is None:
            raise RecursoNoEncontrado(f"La categoría con id {categoria_id} no existe")
        if caja_id is not None and self.repositorio_cajas.obtener_por_id(caja_id) is None:
            raise RecursoNoEncontrado(f"La caja con id {caja_id} no existe")

    def _alertas(self, movimiento: Movimiento) -> List[str]:
        if movimiento.tipo != TipoMovimiento.GASTO:
            return []
        anio, mes = movimiento.fecha.year, movimiento.fecha.month
        alertas = [
            self.servicio_presupuestos.alerta_si_excedido(anio, mes),
            self.servicio_presupuestos_categoria.alerta_si_excedido(movimiento.categoria_id, anio, mes),
        ]
        return [alerta for alerta in alertas if alerta]
