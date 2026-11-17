from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Presupuesto


class RepositorioPresupuestos:
    """Operaciones sobre los presupuestos de UN usuario."""

    def __init__(self, db: Session, usuario_id: int):
        self.db = db
        self.usuario_id = usuario_id

    def _consulta(self):
        return self.db.query(Presupuesto).filter(
            Presupuesto.usuario_id == self.usuario_id
        )

    def crear(self, mes: str, limite: Decimal) -> Presupuesto:
        presupuesto = Presupuesto(mes=mes, limite=limite, usuario_id=self.usuario_id)
        self.db.add(presupuesto)
        self.db.commit()
        self.db.refresh(presupuesto)
        return presupuesto

    def obtener_por_id(self, presupuesto_id: int) -> Optional[Presupuesto]:
        return self._consulta().filter(Presupuesto.id == presupuesto_id).first()

    def obtener_por_mes(self, mes: str) -> Optional[Presupuesto]:
        return self._consulta().filter(Presupuesto.mes == mes).first()

    def listar(self) -> List[Presupuesto]:
        return self._consulta().order_by(Presupuesto.mes).all()

    def actualizar(self, presupuesto: Presupuesto, **cambios) -> Presupuesto:
        for campo, valor in cambios.items():
            setattr(presupuesto, campo, valor)
        self.db.commit()
        self.db.refresh(presupuesto)
        return presupuesto

    def eliminar(self, presupuesto: Presupuesto) -> None:
        self.db.delete(presupuesto)
        self.db.commit()
