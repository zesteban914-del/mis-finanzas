from datetime import date
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from app.controllers.dependencias import servicio
from app.permisos import Funcion, Permiso
from app.schemas import (
    MovimientoActualizar,
    MovimientoCreadoRespuesta,
    MovimientoCrear,
    MovimientoRespuesta,
)
from app.services import ServicioComprobantes, ServicioMovimientos
from app.services.negocio_servicio import TAMANO_MAXIMO

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])

leer = servicio(ServicioMovimientos, Permiso.VER_MOVIMIENTOS)
registrar = servicio(ServicioMovimientos, Permiso.REGISTRAR_MOVIMIENTOS)
gestionar = servicio(ServicioMovimientos, Permiso.GESTIONAR)


@router.post("", response_model=MovimientoCreadoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_movimiento(datos: MovimientoCrear, servicio: ServicioMovimientos = Depends(registrar)):
    movimiento, alertas = servicio.crear(datos)
    return MovimientoCreadoRespuesta(
        movimiento=MovimientoRespuesta.model_validate(movimiento),
        alerta_presupuesto=alertas[0] if alertas else None,
        alertas=alertas,
    )


@router.get("", response_model=List[MovimientoRespuesta])
def listar_movimientos(
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    categoria_id: Optional[int] = Query(default=None),
    caja_id: Optional[int] = Query(default=None),
    servicio: ServicioMovimientos = Depends(leer),
):
    return servicio.listar(fecha_inicio, fecha_fin, categoria_id, caja_id)


@router.get("/{movimiento_id}", response_model=MovimientoRespuesta)
def obtener_movimiento(movimiento_id: int, servicio: ServicioMovimientos = Depends(leer)):
    return servicio.obtener(movimiento_id)


@router.put("/{movimiento_id}", response_model=MovimientoRespuesta)
def actualizar_movimiento(
    movimiento_id: int,
    datos: MovimientoActualizar,
    servicio: ServicioMovimientos = Depends(gestionar),
):
    return servicio.actualizar(movimiento_id, datos)


@router.delete("/{movimiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_movimiento(movimiento_id: int, servicio: ServicioMovimientos = Depends(gestionar)):
    servicio.eliminar(movimiento_id)


# Comprobantes (cuentas de negocio, plan Pro) ---------------------------------
@router.post("/{movimiento_id}/comprobante", status_code=status.HTTP_201_CREATED, tags=["Comprobantes"])
async def subir_comprobante(
    movimiento_id: int,
    archivo: UploadFile = File(description="Imagen JPG/PNG/WEBP o PDF de hasta 2 MB"),
    servicio: ServicioComprobantes = Depends(
        servicio(ServicioComprobantes, Permiso.REGISTRAR_MOVIMIENTOS, Funcion.COMPROBANTES)
    ),
):
    contenido = await archivo.read(TAMANO_MAXIMO + 1)
    comprobante = servicio.subir(movimiento_id, archivo.filename, archivo.content_type, contenido)
    return {"nombre_archivo": comprobante.nombre_archivo, "tamano": comprobante.tamano}


@router.get("/{movimiento_id}/comprobante", tags=["Comprobantes"])
def descargar_comprobante(
    movimiento_id: int,
    servicio: ServicioComprobantes = Depends(
        servicio(ServicioComprobantes, Permiso.VER_MOVIMIENTOS, Funcion.COMPROBANTES)
    ),
):
    comprobante = servicio.obtener(movimiento_id)
    return Response(
        content=comprobante.contenido,
        media_type=comprobante.tipo_contenido,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(comprobante.nombre_archivo)}"
        },
    )


@router.delete("/{movimiento_id}/comprobante", status_code=status.HTTP_204_NO_CONTENT, tags=["Comprobantes"])
def eliminar_comprobante(
    movimiento_id: int,
    servicio: ServicioComprobantes = Depends(
        servicio(ServicioComprobantes, Permiso.GESTIONAR, Funcion.COMPROBANTES)
    ),
):
    servicio.eliminar(movimiento_id)
