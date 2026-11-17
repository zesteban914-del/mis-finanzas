"""Metas de ahorro (cuentas personales) y deudas (ambos tipos de cuenta)."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Deuda, EstadoDeuda, Meta, TipoDeuda, Usuario
from app.repositories import RepositorioDeudas, RepositorioMetas
from app.schemas import DeudaActualizar, DeudaCrear, MetaActualizar, MetaCrear
from app.services.autorizacion import exigir_cupo
from app.services.excepciones import ErrorDeValidacion, RecursoNoEncontrado
from app.services.presupuesto_servicio import formato_pesos
from app.services.validaciones import texto_obligatorio, validar_positivo


class ServicioMetas:
    def __init__(self, db: Session, usuario: Usuario):
        self.plan = usuario.plan_efectivo
        self.repositorio = RepositorioMetas(db, usuario.titular_id)

    def crear(self, datos: MetaCrear) -> Meta:
        nombre = texto_obligatorio(datos.nombre, "nombre")
        validar_positivo(datos.monto_objetivo, "El monto objetivo debe ser mayor que 0")
        self._validar_fecha(datos.fecha_limite)
        exigir_cupo(self.plan, "metas", self.repositorio.contar())
        return self.repositorio.crear(
            nombre=nombre, monto_objetivo=datos.monto_objetivo, fecha_limite=datos.fecha_limite
        )

    def listar(self) -> List[Meta]:
        return self.repositorio.listar()

    def obtener(self, meta_id: int) -> Meta:
        meta = self.repositorio.obtener_por_id(meta_id)
        if meta is None:
            raise RecursoNoEncontrado(f"La meta con id {meta_id} no existe")
        return meta

    def actualizar(self, meta_id: int, datos: MetaActualizar) -> Meta:
        meta = self.obtener(meta_id)
        cambios = datos.model_dump(exclude_unset=True)
        if "nombre" in cambios:
            cambios["nombre"] = texto_obligatorio(cambios["nombre"], "nombre")
        if "monto_objetivo" in cambios:
            validar_positivo(cambios["monto_objetivo"], "El monto objetivo debe ser mayor que 0")
        if cambios.get("fecha_limite"):
            self._validar_fecha(cambios["fecha_limite"])
        return self.repositorio.actualizar(meta, **cambios)

    def aportar(self, meta_id: int, monto: Decimal) -> Meta:
        meta = self.obtener(meta_id)
        validar_positivo(monto, "El aporte debe ser mayor que 0")
        return self.repositorio.actualizar(
            meta, monto_ahorrado=Decimal(meta.monto_ahorrado) + monto
        )

    def eliminar(self, meta_id: int) -> None:
        self.repositorio.eliminar(self.obtener(meta_id))

    @staticmethod
    def _validar_fecha(fecha: Optional[date]) -> None:
        if fecha is not None and fecha < date.today():
            raise ErrorDeValidacion("La fecha límite no puede estar en el pasado")


class ServicioDeudas:
    def __init__(self, db: Session, usuario: Usuario):
        self.repositorio = RepositorioDeudas(db, usuario.titular_id)

    def crear(self, datos: DeudaCrear) -> Deuda:
        contraparte = texto_obligatorio(datos.contraparte, "persona o empresa")
        validar_positivo(datos.monto_total, "El monto debe ser mayor que 0")
        return self.repositorio.crear(
            **datos.model_dump(exclude={"contraparte"}), contraparte=contraparte
        )

    def listar(self, tipo: Optional[TipoDeuda] = None) -> List[Deuda]:
        deudas = self.repositorio.listar()
        if tipo is not None:
            deudas = [d for d in deudas if d.tipo == tipo]
        # Primero las vencidas, luego las pendientes y al final las pagadas.
        orden = {EstadoDeuda.VENCIDA: 0, EstadoDeuda.PENDIENTE: 1, EstadoDeuda.PAGADA: 2}
        return sorted(deudas, key=lambda d: (orden[d.estado], d.fecha_vencimiento or date.max))

    def obtener(self, deuda_id: int) -> Deuda:
        deuda = self.repositorio.obtener_por_id(deuda_id)
        if deuda is None:
            raise RecursoNoEncontrado(f"El registro con id {deuda_id} no existe")
        return deuda

    def actualizar(self, deuda_id: int, datos: DeudaActualizar) -> Deuda:
        deuda = self.obtener(deuda_id)
        cambios = datos.model_dump(exclude_unset=True)
        if "contraparte" in cambios:
            cambios["contraparte"] = texto_obligatorio(cambios["contraparte"], "persona o empresa")
        if "monto_total" in cambios:
            validar_positivo(cambios["monto_total"], "El monto debe ser mayor que 0")
            if cambios["monto_total"] < Decimal(deuda.monto_pagado):
                raise ErrorDeValidacion("El monto total no puede ser menor que lo ya abonado")
        return self.repositorio.actualizar(deuda, **cambios)

    def abonar(self, deuda_id: int, monto: Decimal) -> Deuda:
        deuda = self.obtener(deuda_id)
        validar_positivo(monto, "El abono debe ser mayor que 0")
        if deuda.estado == EstadoDeuda.PAGADA:
            raise ErrorDeValidacion("Este registro ya está saldado")
        if monto > deuda.pendiente:
            raise ErrorDeValidacion(
                f"El abono ({formato_pesos(monto)}) supera el saldo pendiente "
                f"({formato_pesos(deuda.pendiente)})"
            )
        return self.repositorio.actualizar(deuda, monto_pagado=Decimal(deuda.monto_pagado) + monto)

    def eliminar(self, deuda_id: int) -> None:
        self.repositorio.eliminar(self.obtener(deuda_id))
