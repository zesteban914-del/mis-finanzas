from fastapi import APIRouter, Depends, Query

from app.controllers.dependencias import servicio_reportes
from app.schemas import ResumenMensual, SaldoRespuesta
from app.services import ServicioReportes

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/saldo", response_model=SaldoRespuesta)
def consultar_saldo(servicio: ServicioReportes = Depends(servicio_reportes)):
    """Saldo actual: total de ingresos menos total de gastos."""
    return servicio.saldo()


@router.get("/resumen-mensual", response_model=ResumenMensual)
def resumen_mensual(
    mes: str = Query(description="Mes en formato AAAA-MM, por ejemplo 2026-11"),
    servicio: ServicioReportes = Depends(servicio_reportes),
):
    """Totales del mes agrupados por categoría."""
    return servicio.resumen_mensual(mes)
