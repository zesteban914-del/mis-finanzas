from typing import List

from sqlalchemy.orm import Session

from app.models import Categoria, Usuario
from app.repositories import RepositorioCategorias, RepositorioMovimientos, RepositorioRecurrentes
from app.schemas import CategoriaCrear
from app.services.excepciones import ConflictoDeDatos, RecursoNoEncontrado
from app.services.validaciones import texto_obligatorio


class ServicioCategorias:
    """Reglas de negocio de las categorías."""

    def __init__(self, db: Session, usuario: Usuario):
        self.repositorio = RepositorioCategorias(db, usuario.titular_id)
        self.repositorio_movimientos = RepositorioMovimientos(db, usuario.titular_id)
        self.repositorio_recurrentes = RepositorioRecurrentes(db, usuario.titular_id)

    def crear(self, datos: CategoriaCrear) -> Categoria:
        nombre = texto_obligatorio(datos.nombre, "nombre")
        self._validar_nombre_disponible(nombre)
        return self.repositorio.crear(nombre=nombre)

    def obtener(self, categoria_id: int) -> Categoria:
        categoria = self.repositorio.obtener_por_id(categoria_id)
        if categoria is None:
            raise RecursoNoEncontrado(f"La categoría con id {categoria_id} no existe")
        return categoria

    def listar(self) -> List[Categoria]:
        return self.repositorio.listar()

    def actualizar(self, categoria_id: int, datos: CategoriaCrear) -> Categoria:
        categoria = self.obtener(categoria_id)
        nombre = texto_obligatorio(datos.nombre, "nombre")
        if nombre != categoria.nombre:
            self._validar_nombre_disponible(nombre)
        return self.repositorio.actualizar(categoria, nombre=nombre)

    def eliminar(self, categoria_id: int) -> None:
        categoria = self.obtener(categoria_id)
        cantidad = self.repositorio_movimientos.contar_por_categoria(categoria_id)
        if cantidad > 0:
            raise ConflictoDeDatos(
                f"No se puede eliminar la categoría '{categoria.nombre}' "
                f"porque tiene {cantidad} movimiento(s) asociado(s)"
            )
        if self.repositorio_recurrentes.contar_por_categoria(categoria_id) > 0:
            raise ConflictoDeDatos(
                f"No se puede eliminar la categoría '{categoria.nombre}' "
                "porque la usa un movimiento recurrente"
            )
        self.repositorio.eliminar(categoria)

    def _validar_nombre_disponible(self, nombre: str) -> None:
        if self.repositorio.obtener_por_nombre(nombre) is not None:
            raise ConflictoDeDatos(f"Ya existe una categoría con el nombre '{nombre}'")
