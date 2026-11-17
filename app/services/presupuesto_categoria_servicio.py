from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Usuario
from app.repositories import (
    RepositorioCategorias,
    RepositorioMovimientos,
    RepositorioPresupuestosCategoria,
)
from app.schemas import EstadoPresupuestoCategoria
from app.services.excepciones import RecursoNoEncontrado
from app.services.presupuesto_servicio import formato_pesos
from app.services.validaciones import mes_de, validar_mes, validar_positivo


class ServicioPresupuestosCategoria:
    """Límite mensual por categoría (ej. máximo $600.000 en Comida cada mes)."""

    def __init__(self, db: Session, usuario: Usuario):
        self.repositorio = RepositorioPresupuestosCategoria(db, usuario.titular_id)
        self.repositorio_categorias = RepositorioCategorias(db, usuario.titular_id)
        self.repositorio_movimientos = RepositorioMovimientos(db, usuario.titular_id)

    def definir(self, categoria_id: int, limite: Decimal) -> EstadoPresupuestoCategoria:
        """Crea o actualiza el límite de la categoría."""
        if self.repositorio_categorias.obtener_por_id(categoria_id) is None:
            raise RecursoNoEncontrado(f"La categoría con id {categoria_id} no existe")
        validar_positivo(limite, "El límite debe ser mayor que 0")
        existente = self.repositorio.obtener_por_categoria(categoria_id)
        if existente:
            self.repositorio.actualizar(existente, limite=limite)
        else:
            self.repositorio.crear(categoria_id=categoria_id, limite=limite)
        return next(e for e in self.estado_del_mes(None) if e.categoria_id == categoria_id)

    def eliminar(self, categoria_id: int) -> None:
        existente = self.repositorio.obtener_por_categoria(categoria_id)
        if existente is None:
            raise RecursoNoEncontrado("Esa categoría no tiene presupuesto definido")
        self.repositorio.eliminar(existente)

    def estado_del_mes(self, mes: Optional[str]) -> List[EstadoPresupuestoCategoria]:
        anio, numero = validar_mes(mes or mes_de(date.today()))
        gastos = self.repositorio_movimientos.gastos_por_categoria(anio, numero)
        nombres = {c.id: c.nombre for c in self.repositorio_categorias.listar()}
        estados = []
        for presupuesto in self.repositorio.listar():
            limite = Decimal(presupuesto.limite)
            gastado = gastos.get(presupuesto.categoria_id, Decimal(0))
            estados.append(
                EstadoPresupuestoCategoria(
                    categoria_id=presupuesto.categoria_id,
                    categoria=nombres.get(presupuesto.categoria_id, "—"),
                    limite=limite,
                    gastado=gastado,
                    disponible=limite - gastado,
                    porcentaje=int(gastado * 100 / limite),
                    excedido=gastado > limite,
                )
            )
        return sorted(estados, key=lambda e: e.porcentaje, reverse=True)

    def alerta_si_excedido(self, categoria_id: int, anio: int, mes: int) -> Optional[str]:
        presupuesto = self.repositorio.obtener_por_categoria(categoria_id)
        if presupuesto is None:
            return None
        gastado = self.repositorio_movimientos.gastos_por_categoria(anio, mes).get(categoria_id, Decimal(0))
        if gastado > presupuesto.limite:
            categoria = self.repositorio_categorias.obtener_por_id(categoria_id)
            return (
                f"Superaste el límite de «{categoria.nombre}»: llevas "
                f"{formato_pesos(gastado)} de {formato_pesos(presupuesto.limite)} este mes"
            )
        return None
