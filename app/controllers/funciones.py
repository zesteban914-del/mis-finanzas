"""Endpoints de las funciones adicionales: recurrentes, metas, deudas y cajas."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.controllers.dependencias import servicio
from app.models import TipoDeuda
from app.permisos import Funcion, Permiso
from app.schemas import (
    Aporte,
    CajaActualizar,
    CajaCrear,
    CajaRespuesta,
    DeudaActualizar,
    DeudaCrear,
    DeudaRespuesta,
    GeneracionRespuesta,
    MetaActualizar,
    MetaCrear,
    MetaRespuesta,
    RecurrenteActualizar,
    RecurrenteCrear,
    RecurrenteRespuesta,
    TransferenciaCrear,
    TransferenciaRespuesta,
)
from app.services import ServicioCajas, ServicioDeudas, ServicioMetas, ServicioRecurrentes

# Movimientos recurrentes -----------------------------------------------------
recurrentes = APIRouter(prefix="/recurrentes", tags=["Recurrentes"])
leer_recurrentes = servicio(ServicioRecurrentes, Permiso.VER_REPORTES)
gestionar_recurrentes = servicio(ServicioRecurrentes, Permiso.GESTIONAR)


@recurrentes.get("", response_model=List[RecurrenteRespuesta])
def listar_recurrentes(s: ServicioRecurrentes = Depends(leer_recurrentes)):
    return s.listar()


@recurrentes.post("", response_model=RecurrenteRespuesta, status_code=status.HTTP_201_CREATED)
def crear_recurrente(datos: RecurrenteCrear, s: ServicioRecurrentes = Depends(gestionar_recurrentes)):
    return s.crear(datos)


@recurrentes.post("/generar", response_model=GeneracionRespuesta)
def generar_pendientes(
    s: ServicioRecurrentes = Depends(servicio(ServicioRecurrentes, Permiso.VER_MOVIMIENTOS)),
):
    """Registra los movimientos recurrentes pendientes hasta hoy (la interfaz lo llama al abrir)."""
    return GeneracionRespuesta(movimientos_creados=s.generar_pendientes())


@recurrentes.patch("/{recurrente_id}", response_model=RecurrenteRespuesta)
def actualizar_recurrente(
    recurrente_id: int, datos: RecurrenteActualizar, s: ServicioRecurrentes = Depends(gestionar_recurrentes)
):
    return s.actualizar(recurrente_id, datos)


@recurrentes.delete("/{recurrente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_recurrente(recurrente_id: int, s: ServicioRecurrentes = Depends(gestionar_recurrentes)):
    s.eliminar(recurrente_id)


# Metas de ahorro (cuentas personales) ------------------------------------------
metas = APIRouter(prefix="/metas", tags=["Metas de ahorro"])
leer_metas = servicio(ServicioMetas, Permiso.VER_REPORTES, Funcion.METAS)
gestionar_metas = servicio(ServicioMetas, Permiso.GESTIONAR, Funcion.METAS)


@metas.get("", response_model=List[MetaRespuesta])
def listar_metas(s: ServicioMetas = Depends(leer_metas)):
    return s.listar()


@metas.post("", response_model=MetaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_meta(datos: MetaCrear, s: ServicioMetas = Depends(gestionar_metas)):
    return s.crear(datos)


@metas.post("/{meta_id}/aportes", response_model=MetaRespuesta)
def aportar_a_meta(meta_id: int, datos: Aporte, s: ServicioMetas = Depends(gestionar_metas)):
    return s.aportar(meta_id, datos.monto)


@metas.patch("/{meta_id}", response_model=MetaRespuesta)
def actualizar_meta(meta_id: int, datos: MetaActualizar, s: ServicioMetas = Depends(gestionar_metas)):
    return s.actualizar(meta_id, datos)


@metas.delete("/{meta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_meta(meta_id: int, s: ServicioMetas = Depends(gestionar_metas)):
    s.eliminar(meta_id)


# Deudas y préstamos / cuentas por pagar y por cobrar ----------------------------
deudas = APIRouter(prefix="/deudas", tags=["Deudas y cuentas por cobrar/pagar"])
leer_deudas = servicio(ServicioDeudas, Permiso.VER_REPORTES)
gestionar_deudas = servicio(ServicioDeudas, Permiso.GESTIONAR)


@deudas.get("", response_model=List[DeudaRespuesta])
def listar_deudas(
    tipo: Optional[TipoDeuda] = Query(default=None), s: ServicioDeudas = Depends(leer_deudas)
):
    return s.listar(tipo)


@deudas.post("", response_model=DeudaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_deuda(datos: DeudaCrear, s: ServicioDeudas = Depends(gestionar_deudas)):
    return s.crear(datos)


@deudas.post("/{deuda_id}/abonos", response_model=DeudaRespuesta)
def abonar(deuda_id: int, datos: Aporte, s: ServicioDeudas = Depends(gestionar_deudas)):
    return s.abonar(deuda_id, datos.monto)


@deudas.patch("/{deuda_id}", response_model=DeudaRespuesta)
def actualizar_deuda(deuda_id: int, datos: DeudaActualizar, s: ServicioDeudas = Depends(gestionar_deudas)):
    return s.actualizar(deuda_id, datos)


@deudas.delete("/{deuda_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_deuda(deuda_id: int, s: ServicioDeudas = Depends(gestionar_deudas)):
    s.eliminar(deuda_id)


# Cajas y transferencias (cuentas de negocio) -----------------------------------
cajas = APIRouter(prefix="/cajas", tags=["Cajas"])
leer_cajas = servicio(ServicioCajas, Permiso.VER_MOVIMIENTOS, Funcion.CAJAS)
reportes_cajas = servicio(ServicioCajas, Permiso.VER_REPORTES, Funcion.CAJAS)
gestionar_cajas = servicio(ServicioCajas, Permiso.GESTIONAR, Funcion.CAJAS)


@cajas.get("", response_model=List[CajaRespuesta])
def listar_cajas(s: ServicioCajas = Depends(leer_cajas)):
    return s.listar()


@cajas.post("", response_model=CajaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_caja(datos: CajaCrear, s: ServicioCajas = Depends(gestionar_cajas)):
    return s.crear(datos)


@cajas.get("/transferencias", response_model=List[TransferenciaRespuesta])
def listar_transferencias(s: ServicioCajas = Depends(reportes_cajas)):
    return s.listar_transferencias()


@cajas.post("/transferencias", response_model=TransferenciaRespuesta, status_code=status.HTTP_201_CREATED)
def transferir(datos: TransferenciaCrear, s: ServicioCajas = Depends(gestionar_cajas)):
    return s.transferir(datos)


@cajas.patch("/{caja_id}", response_model=CajaRespuesta)
def actualizar_caja(caja_id: int, datos: CajaActualizar, s: ServicioCajas = Depends(gestionar_cajas)):
    return s.actualizar(caja_id, datos)


@cajas.delete("/{caja_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_caja(caja_id: int, s: ServicioCajas = Depends(gestionar_cajas)):
    s.eliminar(caja_id)
