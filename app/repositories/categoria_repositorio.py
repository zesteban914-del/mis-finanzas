from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models import Categoria


class RepositorioCategorias:
    """Operaciones sobre las categorías de UN usuario.

    Todas las consultas parten de `_consulta()`, que filtra por usuario: es
    imposible leer o modificar las categorías de otra persona.
    """

    def __init__(self, db: Session, usuario_id: int):
        self.db = db
        self.usuario_id = usuario_id

    def _consulta(self):
        return self.db.query(Categoria).filter(Categoria.usuario_id == self.usuario_id)

    def crear(self, nombre: str) -> Categoria:
        categoria = Categoria(nombre=nombre, usuario_id=self.usuario_id)
        self.db.add(categoria)
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def crear_varias(self, nombres: Iterable[str]) -> None:
        self.db.add_all(Categoria(nombre=n, usuario_id=self.usuario_id) for n in nombres)
        self.db.commit()

    def obtener_por_id(self, categoria_id: int) -> Optional[Categoria]:
        return self._consulta().filter(Categoria.id == categoria_id).first()

    def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        return self._consulta().filter(Categoria.nombre == nombre).first()

    def listar(self) -> List[Categoria]:
        return self._consulta().order_by(Categoria.nombre).all()

    def actualizar(self, categoria: Categoria, nombre: str) -> Categoria:
        categoria.nombre = nombre
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def eliminar(self, categoria: Categoria) -> None:
        self.db.delete(categoria)
        self.db.commit()
