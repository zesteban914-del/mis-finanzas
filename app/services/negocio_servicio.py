"""Funciones de las cuentas de negocio: cajas, transferencias y comprobantes."""

from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from app.models import Comprobante, TipoMovimiento, Transferencia, Usuario
from app.repositories import (
    RepositorioCajas,
    RepositorioComprobantes,
    RepositorioMovimientos,
    RepositorioTransferencias,
)
from app.schemas import CajaActualizar, CajaCrear, CajaRespuesta, TransferenciaCrear
from app.services.autorizacion import exigir_caracteristica, exigir_cupo
from app.services.excepciones import ConflictoDeDatos, ErrorDeValidacion, RecursoNoEncontrado
from app.services.presupuesto_servicio import formato_pesos
from app.services.validaciones import texto_obligatorio, validar_no_futura, validar_positivo

TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
TAMANO_MAXIMO = 2 * 1024 * 1024  # 2 MB


class ServicioCajas:
    """Saldo de cada caja = saldo inicial + ingresos − gastos + transferencias recibidas − enviadas."""

    def __init__(self, db: Session, usuario: Usuario):
        self.plan = usuario.plan_efectivo
        self.repositorio = RepositorioCajas(db, usuario.titular_id)
        self.transferencias = RepositorioTransferencias(db, usuario.titular_id)
        self.movimientos = RepositorioMovimientos(db, usuario.titular_id)

    def crear(self, datos: CajaCrear) -> CajaRespuesta:
        nombre = texto_obligatorio(datos.nombre, "nombre")
        self._validar_saldo_inicial(datos.saldo_inicial)
        if self.repositorio.obtener_por_nombre(nombre):
            raise ConflictoDeDatos(f"Ya existe una caja llamada '{nombre}'")
        exigir_cupo(self.plan, "cajas", self.repositorio.contar())
        caja = self.repositorio.crear(nombre=nombre, tipo=datos.tipo, saldo_inicial=datos.saldo_inicial)
        return self._con_saldo(caja, self._saldos())

    def listar(self) -> List[CajaRespuesta]:
        saldos = self._saldos()
        return [self._con_saldo(caja, saldos) for caja in self.repositorio.listar()]

    def obtener(self, caja_id: int):
        caja = self.repositorio.obtener_por_id(caja_id)
        if caja is None:
            raise RecursoNoEncontrado(f"La caja con id {caja_id} no existe")
        return caja

    def actualizar(self, caja_id: int, datos: CajaActualizar) -> CajaRespuesta:
        caja = self.obtener(caja_id)
        cambios = datos.model_dump(exclude_none=True)
        if "nombre" in cambios:
            cambios["nombre"] = texto_obligatorio(cambios["nombre"], "nombre")
            otra = self.repositorio.obtener_por_nombre(cambios["nombre"])
            if otra and otra.id != caja.id:
                raise ConflictoDeDatos(f"Ya existe una caja llamada '{cambios['nombre']}'")
        if "saldo_inicial" in cambios:
            self._validar_saldo_inicial(cambios["saldo_inicial"])
        caja = self.repositorio.actualizar(caja, **cambios)
        return self._con_saldo(caja, self._saldos())

    def eliminar(self, caja_id: int) -> None:
        caja = self.obtener(caja_id)
        if self.movimientos.contar_por_caja(caja_id) or self.transferencias.contar_por_caja(caja_id):
            raise ConflictoDeDatos(
                f"No se puede eliminar la caja '{caja.nombre}' porque tiene movimientos o transferencias"
            )
        self.repositorio.eliminar(caja)

    def transferir(self, datos: TransferenciaCrear) -> Transferencia:
        if datos.origen_id == datos.destino_id:
            raise ErrorDeValidacion("La caja de origen y la de destino deben ser distintas")
        origen = self.obtener(datos.origen_id)
        self.obtener(datos.destino_id)
        validar_positivo(datos.monto, "El monto debe ser mayor que 0")
        validar_no_futura(datos.fecha, "La fecha de la transferencia no puede ser futura")
        disponible = self._saldos().get(origen.id, Decimal(0)) + Decimal(origen.saldo_inicial)
        if datos.monto > disponible:
            raise ErrorDeValidacion(
                f"Saldo insuficiente en '{origen.nombre}': tiene {formato_pesos(disponible)}"
            )
        return self.transferencias.crear(**datos.model_dump())

    def listar_transferencias(self) -> List[Transferencia]:
        return self.transferencias.listar()

    def _saldos(self) -> dict:
        """{caja_id: cambio neto por movimientos y transferencias} (sin saldo inicial)."""
        neto = dict(self.transferencias.entradas_y_salidas())
        for (caja_id, tipo), total in self.movimientos.totales_por_caja().items():
            signo = 1 if tipo == TipoMovimiento.INGRESO else -1
            neto[caja_id] = neto.get(caja_id, Decimal(0)) + signo * total
        return neto

    @staticmethod
    def _con_saldo(caja, saldos: dict) -> CajaRespuesta:
        inicial = Decimal(caja.saldo_inicial)
        return CajaRespuesta(
            id=caja.id,
            nombre=caja.nombre,
            tipo=caja.tipo,
            saldo_inicial=inicial,
            saldo_actual=inicial + saldos.get(caja.id, Decimal(0)),
        )

    @staticmethod
    def _validar_saldo_inicial(valor: Decimal) -> None:
        if valor is None or valor < 0:
            raise ErrorDeValidacion("El saldo inicial no puede ser negativo")


class ServicioComprobantes:
    """Foto o PDF de la factura de un movimiento (plan Pro)."""

    def __init__(self, db: Session, usuario: Usuario):
        self.plan = usuario.plan_efectivo
        self.movimientos = RepositorioMovimientos(db, usuario.titular_id)
        self.repositorio = RepositorioComprobantes(db)

    def subir(self, movimiento_id: int, nombre: str, tipo: str, contenido: bytes) -> Comprobante:
        exigir_caracteristica(self.plan, "comprobantes")
        movimiento = self._movimiento(movimiento_id)
        if tipo not in TIPOS_PERMITIDOS:
            raise ErrorDeValidacion("Solo se permiten imágenes JPG, PNG o WEBP, o archivos PDF")
        if not contenido:
            raise ErrorDeValidacion("El archivo está vacío")
        if len(contenido) > TAMANO_MAXIMO:
            raise ErrorDeValidacion("El archivo no puede pesar más de 2 MB")
        return self.repositorio.guardar(movimiento, (nombre or "comprobante")[:150], tipo, contenido)

    def obtener(self, movimiento_id: int) -> Comprobante:
        movimiento = self._movimiento(movimiento_id)
        if movimiento.comprobante is None:
            raise RecursoNoEncontrado("Este movimiento no tiene comprobante")
        return movimiento.comprobante

    def eliminar(self, movimiento_id: int) -> None:
        self.repositorio.eliminar(self.obtener(movimiento_id))

    def _movimiento(self, movimiento_id: int):
        movimiento = self.movimientos.obtener_por_id(movimiento_id)
        if movimiento is None:
            raise RecursoNoEncontrado(f"El movimiento con id {movimiento_id} no existe")
        return movimiento
