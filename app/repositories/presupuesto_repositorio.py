from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Presupuesto


class RepositorioPresupuestos:
    """Operaciones de base de datos sobre la tabla de presupuestos."""

    def __init__(self, db: Session):
        self.db = db

    def crear(self, mes: str, limite: Decimal) -> Presupuesto:
        presupuesto = Presupuesto(mes=mes, limite=limite)
        self.db.add(presupuesto)
        self.db.commit()
        self.db.refresh(presupuesto)
        return presupuesto

    def obtener_por_id(self, presupuesto_id: int) -> Optional[Presupuesto]:
        return self.db.get(Presupuesto, presupuesto_id)

    def obtener_por_mes(self, mes: str) -> Optional[Presupuesto]:
        return self.db.query(Presupuesto).filter(Presupuesto.mes == mes).first()

    def listar(self) -> List[Presupuesto]:
        return self.db.query(Presupuesto).order_by(Presupuesto.mes).all()

    def actualizar(self, presupuesto: Presupuesto, **cambios) -> Presupuesto:
        for campo, valor in cambios.items():
            setattr(presupuesto, campo, valor)
        self.db.commit()
        self.db.refresh(presupuesto)
        return presupuesto

    def eliminar(self, presupuesto: Presupuesto) -> None:
        self.db.delete(presupuesto)
        self.db.commit()
