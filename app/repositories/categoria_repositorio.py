from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Categoria


class RepositorioCategorias:
    """Operaciones de base de datos sobre la tabla de categorías."""

    def __init__(self, db: Session):
        self.db = db

    def crear(self, nombre: str) -> Categoria:
        categoria = Categoria(nombre=nombre)
        self.db.add(categoria)
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def obtener_por_id(self, categoria_id: int) -> Optional[Categoria]:
        return self.db.get(Categoria, categoria_id)

    def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        return (
            self.db.query(Categoria).filter(Categoria.nombre == nombre).first()
        )

    def listar(self) -> List[Categoria]:
        return self.db.query(Categoria).order_by(Categoria.nombre).all()

    def actualizar(self, categoria: Categoria, nombre: str) -> Categoria:
        categoria.nombre = nombre
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def eliminar(self, categoria: Categoria) -> None:
        self.db.delete(categoria)
        self.db.commit()
