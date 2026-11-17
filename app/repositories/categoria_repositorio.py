from typing import Iterable, List, Optional

from app.models import Categoria
from app.repositories.base import RepositorioDelTitular


class RepositorioCategorias(RepositorioDelTitular):
    """Categorías de un titular."""

    modelo = Categoria

    def crear_varias(self, nombres: Iterable[str]) -> None:
        self.db.add_all(Categoria(nombre=n, usuario_id=self.titular_id) for n in nombres)
        self.db.commit()

    def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        return self._consulta().filter(Categoria.nombre == nombre).first()

    def listar(self) -> List[Categoria]:
        return super().listar(Categoria.nombre)
