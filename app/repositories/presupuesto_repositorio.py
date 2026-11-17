from typing import List, Optional

from app.models import Presupuesto
from app.repositories.base import RepositorioDelTitular


class RepositorioPresupuestos(RepositorioDelTitular):
    """Presupuestos mensuales de un titular."""

    modelo = Presupuesto

    def obtener_por_mes(self, mes: str) -> Optional[Presupuesto]:
        return self._consulta().filter(Presupuesto.mes == mes).first()

    def listar(self) -> List[Presupuesto]:
        return super().listar(Presupuesto.mes)
