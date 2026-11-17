from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.controllers.dependencias import servicio
from app.permisos import Permiso
from app.schemas import (
    EstadoPresupuesto,
    EstadoPresupuestoCategoria,
    PresupuestoCategoriaDefinir,
    PresupuestoCrear,
    PresupuestoRespuesta,
)
from app.services import ServicioPresupuestos, ServicioPresupuestosCategoria

router = APIRouter(prefix="/presupuestos", tags=["Presupuestos"])

leer = servicio(ServicioPresupuestos, Permiso.VER_REPORTES)
gestionar = servicio(ServicioPresupuestos, Permiso.GESTIONAR)
leer_categoria = servicio(ServicioPresupuestosCategoria, Permiso.VER_REPORTES)
gestionar_categoria = servicio(ServicioPresupuestosCategoria, Permiso.GESTIONAR)


@router.post("", response_model=PresupuestoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_presupuesto(datos: PresupuestoCrear, servicio: ServicioPresupuestos = Depends(gestionar)):
    return servicio.crear(datos)


@router.get("", response_model=List[PresupuestoRespuesta])
def listar_presupuestos(servicio: ServicioPresupuestos = Depends(leer)):
    return servicio.listar()


# Presupuesto por categoría (va antes de /{mes} para que "categorias" no se tome como un mes)
@router.get("/categorias", response_model=List[EstadoPresupuestoCategoria])
def estado_por_categoria(
    mes: Optional[str] = Query(default=None, description="AAAA-MM; por defecto el mes actual"),
    servicio: ServicioPresupuestosCategoria = Depends(leer_categoria),
):
    """Límite, gasto y estado de cada categoría con presupuesto."""
    return servicio.estado_del_mes(mes)


@router.put("/categorias/{categoria_id}", response_model=EstadoPresupuestoCategoria)
def definir_por_categoria(
    categoria_id: int,
    datos: PresupuestoCategoriaDefinir,
    servicio: ServicioPresupuestosCategoria = Depends(gestionar_categoria),
):
    """Crea o actualiza el límite mensual de una categoría."""
    return servicio.definir(categoria_id, datos.limite)


@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_por_categoria(
    categoria_id: int, servicio: ServicioPresupuestosCategoria = Depends(gestionar_categoria)
):
    servicio.eliminar(categoria_id)


@router.get("/{mes}/estado", response_model=EstadoPresupuesto)
def estado_presupuesto(mes: str, servicio: ServicioPresupuestos = Depends(leer)):
    """Indica cuánto se ha gastado en el mes y si se superó el límite."""
    return servicio.estado(mes)


@router.put("/{presupuesto_id}", response_model=PresupuestoRespuesta)
def actualizar_presupuesto(
    presupuesto_id: int,
    datos: PresupuestoCrear,
    servicio: ServicioPresupuestos = Depends(gestionar),
):
    return servicio.actualizar(presupuesto_id, datos)


@router.delete("/{presupuesto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_presupuesto(presupuesto_id: int, servicio: ServicioPresupuestos = Depends(gestionar)):
    servicio.eliminar(presupuesto_id)
