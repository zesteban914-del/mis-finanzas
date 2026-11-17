from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.schemas import EstadoPresupuesto, PresupuestoCrear, PresupuestoRespuesta
from app.services import ServicioPresupuestos

router = APIRouter(prefix="/presupuestos", tags=["Presupuestos"])


@router.post(
    "", response_model=PresupuestoRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_presupuesto(datos: PresupuestoCrear, db: Session = Depends(obtener_db)):
    return ServicioPresupuestos(db).crear(datos)


@router.get("", response_model=List[PresupuestoRespuesta])
def listar_presupuestos(db: Session = Depends(obtener_db)):
    return ServicioPresupuestos(db).listar()


@router.get("/{mes}/estado", response_model=EstadoPresupuesto)
def estado_presupuesto(mes: str, db: Session = Depends(obtener_db)):
    """Indica cuánto se ha gastado en el mes y si se superó el límite."""
    return ServicioPresupuestos(db).estado(mes)


@router.put("/{presupuesto_id}", response_model=PresupuestoRespuesta)
def actualizar_presupuesto(
    presupuesto_id: int, datos: PresupuestoCrear, db: Session = Depends(obtener_db)
):
    return ServicioPresupuestos(db).actualizar(presupuesto_id, datos)


@router.delete("/{presupuesto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_presupuesto(presupuesto_id: int, db: Session = Depends(obtener_db)):
    ServicioPresupuestos(db).eliminar(presupuesto_id)
