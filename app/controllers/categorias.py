from typing import List

from fastapi import APIRouter, Depends, status

from app.controllers.dependencias import servicio_categorias
from app.schemas import CategoriaCrear, CategoriaRespuesta
from app.services import ServicioCategorias

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.post("", response_model=CategoriaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    datos: CategoriaCrear, servicio: ServicioCategorias = Depends(servicio_categorias)
):
    return servicio.crear(datos)


@router.get("", response_model=List[CategoriaRespuesta])
def listar_categorias(servicio: ServicioCategorias = Depends(servicio_categorias)):
    return servicio.listar()


@router.get("/{categoria_id}", response_model=CategoriaRespuesta)
def obtener_categoria(
    categoria_id: int, servicio: ServicioCategorias = Depends(servicio_categorias)
):
    return servicio.obtener(categoria_id)


@router.put("/{categoria_id}", response_model=CategoriaRespuesta)
def actualizar_categoria(
    categoria_id: int,
    datos: CategoriaCrear,
    servicio: ServicioCategorias = Depends(servicio_categorias),
):
    return servicio.actualizar(categoria_id, datos)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(
    categoria_id: int, servicio: ServicioCategorias = Depends(servicio_categorias)
):
    servicio.eliminar(categoria_id)
