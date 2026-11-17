from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session


class RepositorioDelTitular:
    """Base de los repositorios cuyos registros pertenecen a un titular.

    El titular es la persona dueña de los datos (o el negocio, si quien
    consulta es un miembro de su equipo). Todas las consultas parten de
    `_consulta()`, que filtra por titular: es imposible leer o modificar
    datos de otra cuenta. Cada subclase solo indica su `modelo`.
    """

    modelo = None

    def __init__(self, db: Session, titular_id: int):
        self.db = db
        self.titular_id = titular_id

    def _consulta(self):
        return self.db.query(self.modelo).filter(self.modelo.usuario_id == self.titular_id)

    def crear(self, **datos):
        registro = self.modelo(**datos, usuario_id=self.titular_id)
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def obtener_por_id(self, registro_id: int) -> Optional[object]:
        return self._consulta().filter(self.modelo.id == registro_id).first()

    def listar(self, *orden) -> List:
        return self._consulta().order_by(*(orden or (self.modelo.id,))).all()

    def actualizar(self, registro, **cambios):
        for campo, valor in cambios.items():
            setattr(registro, campo, valor)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def eliminar(self, registro) -> None:
        self.db.delete(registro)
        self.db.commit()

    def contar(self) -> int:
        return (
            self.db.query(func.count(self.modelo.id))
            .filter(self.modelo.usuario_id == self.titular_id)
            .scalar()
            or 0
        )
