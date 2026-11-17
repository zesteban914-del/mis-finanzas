from typing import List

from fastapi import APIRouter, Depends, status

from app.controllers.dependencias import servicio_presupuestos
from app.schemas import EstadoPresupuesto, PresupuestoCrear, PresupuestoRespuesta
from app.services import ServicioPresupuestos

router = APIRouter(prefix="/presupuestos", tags=["Presupuestos"])


@router.post(
    "", response_model=PresupuestoRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_presupuesto(
    datos: PresupuestoCrear,
    servicio: ServicioPresupuestos = Depends(servicio_presupuestos),
):
    return servicio.crear(datos)


@router.get("", response_model=List[PresupuestoRespuesta])
def listar_presupuestos(servicio: ServicioPresupuestos = Depends(servicio_presupuestos)):
    return servicio.listar()


@router.get("/{mes}/estado", response_model=EstadoPresupuesto)
def estado_presupuesto(
    mes: str, servicio: ServicioPresupuestos = Depends(servicio_presupuestos)
):
    """Indica cuánto se ha gastado en el mes y si se superó el límite."""
    return servicio.estado(mes)


@router.put("/{presupuesto_id}", response_model=PresupuestoRespuesta)
def actualizar_presupuesto(
    presupuesto_id: int,
    datos: PresupuestoCrear,
    servicio: ServicioPresupuestos = Depends(servicio_presupuestos),
):
    return servicio.actualizar(presupuesto_id, datos)


@router.delete("/{presupuesto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_presupuesto(
    presupuesto_id: int, servicio: ServicioPresupuestos = Depends(servicio_presupuestos)
):
    servicio.eliminar(presupuesto_id)
