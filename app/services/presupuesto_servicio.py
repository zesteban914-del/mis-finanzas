from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Presupuesto, TipoMovimiento, Usuario
from app.repositories import RepositorioMovimientos, RepositorioPresupuestos
from app.schemas import EstadoPresupuesto, PresupuestoCrear
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    RecursoNoEncontrado,
)
from app.services.validaciones import validar_mes


def formato_pesos(valor) -> str:
    """1234567.5 → '$1.234.568' (separador de miles con punto, como en Colombia)."""
    return "$" + f"{valor:,.0f}".replace(",", ".")


class ServicioPresupuestos:
    """Reglas de negocio de los presupuestos mensuales (límite total del mes)."""

    def __init__(self, db: Session, usuario: Usuario):
        self.repositorio = RepositorioPresupuestos(db, usuario.titular_id)
        self.repositorio_movimientos = RepositorioMovimientos(db, usuario.titular_id)

    def crear(self, datos: PresupuestoCrear) -> Presupuesto:
        validar_mes(datos.mes)
        self._validar_limite(datos.limite)
        if self.repositorio.obtener_por_mes(datos.mes) is not None:
            raise ConflictoDeDatos(
                f"Ya existe un presupuesto para el mes {datos.mes}"
            )
        return self.repositorio.crear(mes=datos.mes, limite=datos.limite)

    def listar(self) -> List[Presupuesto]:
        return self.repositorio.listar()

    def actualizar(self, presupuesto_id: int, datos: PresupuestoCrear) -> Presupuesto:
        presupuesto = self._obtener(presupuesto_id)
        validar_mes(datos.mes)
        self._validar_limite(datos.limite)
        existente = self.repositorio.obtener_por_mes(datos.mes)
        if existente is not None and existente.id != presupuesto.id:
            raise ConflictoDeDatos(
                f"Ya existe un presupuesto para el mes {datos.mes}"
            )
        return self.repositorio.actualizar(
            presupuesto, mes=datos.mes, limite=datos.limite
        )

    def eliminar(self, presupuesto_id: int) -> None:
        self.repositorio.eliminar(self._obtener(presupuesto_id))

    def estado(self, mes: str) -> EstadoPresupuesto:
        """Compara el límite del mes con los gastos reales de ese mes."""
        anio, numero_mes = validar_mes(mes)
        presupuesto = self.repositorio.obtener_por_mes(mes)
        if presupuesto is None:
            raise RecursoNoEncontrado(f"No hay presupuesto definido para {mes}")
        total_gastado = self.repositorio_movimientos.sumar_por_tipo(
            TipoMovimiento.GASTO, anio, numero_mes
        )
        return EstadoPresupuesto(
            mes=mes,
            limite=presupuesto.limite,
            total_gastado=total_gastado,
            disponible=presupuesto.limite - total_gastado,
            excedido=total_gastado > presupuesto.limite,
        )

    def alerta_si_excedido(self, anio: int, mes: int) -> Optional[str]:
        """Mensaje de alerta si los gastos del mes superan su presupuesto."""
        clave = f"{anio:04d}-{mes:02d}"
        presupuesto = self.repositorio.obtener_por_mes(clave)
        if presupuesto is None:
            return None
        total_gastado = self.repositorio_movimientos.sumar_por_tipo(
            TipoMovimiento.GASTO, anio, mes
        )
        if total_gastado > presupuesto.limite:
            return (
                f"Presupuesto de {clave} superado: llevas "
                f"{formato_pesos(total_gastado)} gastados y el límite es "
                f"{formato_pesos(presupuesto.limite)}"
            )
        return None

    def _obtener(self, presupuesto_id: int) -> Presupuesto:
        presupuesto = self.repositorio.obtener_por_id(presupuesto_id)
        if presupuesto is None:
            raise RecursoNoEncontrado(
                f"El presupuesto con id {presupuesto_id} no existe"
            )
        return presupuesto

    @staticmethod
    def _validar_limite(limite) -> None:
        if limite is None or limite <= 0:
            raise ErrorDeValidacion("El límite del presupuesto debe ser mayor que 0")
