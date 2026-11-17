from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.schemas import ResumenMensual, SaldoRespuesta
from app.services import ServicioReportes

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/saldo", response_model=SaldoRespuesta)
def consultar_saldo(db: Session = Depends(obtener_db)):
    """Saldo actual: total de ingresos menos total de gastos."""
    return ServicioReportes(db).saldo()


@router.get("/resumen-mensual", response_model=ResumenMensual)
def resumen_mensual(
    mes: str = Query(description="Mes en formato AAAA-MM, por ejemplo 2026-11"),
    db: Session = Depends(obtener_db),
):
    """Totales del mes agrupados por categoría."""
    return ServicioReportes(db).resumen_mensual(mes)
