from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.schemas import CategoriaCrear, CategoriaRespuesta
from app.services import ServicioCategorias

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.post("", response_model=CategoriaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_categoria(datos: CategoriaCrear, db: Session = Depends(obtener_db)):
    return ServicioCategorias(db).crear(datos)


@router.get("", response_model=List[CategoriaRespuesta])
def listar_categorias(db: Session = Depends(obtener_db)):
    return ServicioCategorias(db).listar()


@router.get("/{categoria_id}", response_model=CategoriaRespuesta)
def obtener_categoria(categoria_id: int, db: Session = Depends(obtener_db)):
    return ServicioCategorias(db).obtener(categoria_id)


@router.put("/{categoria_id}", response_model=CategoriaRespuesta)
def actualizar_categoria(
    categoria_id: int, datos: CategoriaCrear, db: Session = Depends(obtener_db)
):
    return ServicioCategorias(db).actualizar(categoria_id, datos)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(categoria_id: int, db: Session = Depends(obtener_db)):
    ServicioCategorias(db).eliminar(categoria_id)
