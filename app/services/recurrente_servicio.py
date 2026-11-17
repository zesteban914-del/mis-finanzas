from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Recurrente, Usuario
from app.repositories import (
    RepositorioCajas,
    RepositorioCategorias,
    RepositorioMovimientos,
    RepositorioRecurrentes,
)
from app.schemas import RecurrenteActualizar, RecurrenteCrear
from app.services.autorizacion import exigir_cupo
from app.services.excepciones import ErrorDeValidacion, RecursoNoEncontrado
from app.services.validaciones import mes_de, mes_siguiente, validar_mes, validar_positivo


class ServicioRecurrentes:
    """Movimientos que se repiten cada mes y su registro automático."""

    def __init__(self, db: Session, usuario: Usuario):
        self.plan = usuario.plan_efectivo
        self.repositorio = RepositorioRecurrentes(db, usuario.titular_id)
        self.repositorio_movimientos = RepositorioMovimientos(db, usuario.titular_id)
        self.repositorio_categorias = RepositorioCategorias(db, usuario.titular_id)
        self.repositorio_cajas = RepositorioCajas(db, usuario.titular_id)

    def crear(self, datos: RecurrenteCrear) -> Recurrente:
        self._validar(datos.monto, datos.dia_del_mes, datos.categoria_id, datos.caja_id)
        mes_inicio = datos.mes_inicio or mes_de(date.today())
        validar_mes(mes_inicio)
        if mes_inicio > mes_de(date.today()):
            raise ErrorDeValidacion("El mes de inicio no puede ser futuro")
        exigir_cupo(self.plan, "recurrentes", self.repositorio.contar())
        return self.repositorio.crear(**datos.model_dump(exclude={"mes_inicio"}), mes_inicio=mes_inicio)

    def listar(self) -> List[Recurrente]:
        return self.repositorio.listar()

    def obtener(self, recurrente_id: int) -> Recurrente:
        recurrente = self.repositorio.obtener_por_id(recurrente_id)
        if recurrente is None:
            raise RecursoNoEncontrado(f"El movimiento recurrente con id {recurrente_id} no existe")
        return recurrente

    def actualizar(self, recurrente_id: int, datos: RecurrenteActualizar) -> Recurrente:
        recurrente = self.obtener(recurrente_id)
        cambios = datos.model_dump(exclude_none=True)
        self._validar(
            cambios.get("monto", recurrente.monto),
            cambios.get("dia_del_mes", recurrente.dia_del_mes),
            cambios.get("categoria_id", recurrente.categoria_id),
            recurrente.caja_id,
        )
        return self.repositorio.actualizar(recurrente, **cambios)

    def eliminar(self, recurrente_id: int) -> None:
        """Los movimientos ya generados se conservan."""
        self.repositorio.eliminar(self.obtener(recurrente_id))

    def generar_pendientes(self, hoy: Optional[date] = None) -> int:
        """Registra los movimientos de cada mes pendiente hasta hoy.

        Ejemplo: un arriendo el día 5 creado con inicio en septiembre, si hoy
        es 17 de noviembre, genera septiembre, octubre y noviembre. Si se
        vuelve a llamar no genera nada: `ultimo_mes_generado` ya es noviembre.
        """
        hoy = hoy or date.today()
        creados = 0
        for recurrente in self.repositorio.listar_activos():
            mes = (
                mes_siguiente(recurrente.ultimo_mes_generado)
                if recurrente.ultimo_mes_generado
                else recurrente.mes_inicio
            )
            while mes <= mes_de(hoy):
                anio, numero = validar_mes(mes)
                fecha = date(anio, numero, recurrente.dia_del_mes)
                if fecha > hoy:
                    break
                self.repositorio_movimientos.crear(
                    tipo=recurrente.tipo,
                    monto=recurrente.monto,
                    fecha=fecha,
                    descripcion=recurrente.descripcion,
                    categoria_id=recurrente.categoria_id,
                    caja_id=recurrente.caja_id,
                    recurrente_id=recurrente.id,
                )
                self.repositorio.actualizar(recurrente, ultimo_mes_generado=mes)
                creados += 1
                mes = mes_siguiente(mes)
        return creados

    def _validar(self, monto, dia: int, categoria_id: int, caja_id: Optional[int]) -> None:
        validar_positivo(monto, "El monto debe ser mayor que 0")
        if not 1 <= dia <= 28:
            raise ErrorDeValidacion(
                "El día del mes debe estar entre 1 y 28 (así existe en todos los meses)"
            )
        if self.repositorio_categorias.obtener_por_id(categoria_id) is None:
            raise RecursoNoEncontrado(f"La categoría con id {categoria_id} no existe")
        if caja_id is not None and self.repositorio_cajas.obtener_por_id(caja_id) is None:
            raise RecursoNoEncontrado(f"La caja con id {caja_id} no existe")
