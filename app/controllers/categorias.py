from typing import List

from fastapi import APIRouter, Depends, status

from app.controllers.dependencias import servicio
from app.permisos import Permiso
from app.schemas import CategoriaCrear, CategoriaRespuesta
from app.services import ServicioCategorias

router = APIRouter(prefix="/categorias", tags=["Categorías"])

leer = servicio(ServicioCategorias, Permiso.VER_MOVIMIENTOS)
gestionar = servicio(ServicioCategorias, Permiso.GESTIONAR)


@router.post("", response_model=CategoriaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_categoria(datos: CategoriaCrear, servicio: ServicioCategorias = Depends(gestionar)):
    return servicio.crear(datos)


@router.get("", response_model=List[CategoriaRespuesta])
def listar_categorias(servicio: ServicioCategorias = Depends(leer)):
    return servicio.listar()


@router.get("/{categoria_id}", response_model=CategoriaRespuesta)
def obtener_categoria(categoria_id: int, servicio: ServicioCategorias = Depends(leer)):
    return servicio.obtener(categoria_id)


@router.put("/{categoria_id}", response_model=CategoriaRespuesta)
def actualizar_categoria(
    categoria_id: int, datos: CategoriaCrear, servicio: ServicioCategorias = Depends(gestionar)
):
    return servicio.actualizar(categoria_id, datos)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(categoria_id: int, servicio: ServicioCategorias = Depends(gestionar)):
    servicio.eliminar(categoria_id)
