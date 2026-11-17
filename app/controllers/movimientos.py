from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.schemas import (
    MovimientoActualizar,
    MovimientoCreadoRespuesta,
    MovimientoCrear,
    MovimientoRespuesta,
)
from app.services import ServicioMovimientos

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.post(
    "", response_model=MovimientoCreadoRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_movimiento(datos: MovimientoCrear, db: Session = Depends(obtener_db)):
    movimiento, alerta = ServicioMovimientos(db).crear(datos)
    return MovimientoCreadoRespuesta(
        movimiento=MovimientoRespuesta.model_validate(movimiento),
        alerta_presupuesto=alerta,
    )


@router.get("", response_model=List[MovimientoRespuesta])
def listar_movimientos(
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    categoria_id: Optional[int] = Query(default=None),
    db: Session = Depends(obtener_db),
):
    return ServicioMovimientos(db).listar(fecha_inicio, fecha_fin, categoria_id)


@router.get("/{movimiento_id}", response_model=MovimientoRespuesta)
def obtener_movimiento(movimiento_id: int, db: Session = Depends(obtener_db)):
    return ServicioMovimientos(db).obtener(movimiento_id)


@router.put("/{movimiento_id}", response_model=MovimientoRespuesta)
def actualizar_movimiento(
    movimiento_id: int,
    datos: MovimientoActualizar,
    db: Session = Depends(obtener_db),
):
    return ServicioMovimientos(db).actualizar(movimiento_id, datos)


@router.delete("/{movimiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_movimiento(movimiento_id: int, db: Session = Depends(obtener_db)):
    ServicioMovimientos(db).eliminar(movimiento_id)
