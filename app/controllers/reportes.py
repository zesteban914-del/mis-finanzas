from fastapi import APIRouter, Depends, Query, Response

from app.controllers.dependencias import servicio
from app.permisos import Permiso
from app.schemas import ResumenMensual, SaldoRespuesta
from app.services import ServicioExportacion, ServicioReportes

router = APIRouter(prefix="/reportes", tags=["Reportes"])

leer = servicio(ServicioReportes, Permiso.VER_REPORTES)


@router.get("/saldo", response_model=SaldoRespuesta)
def consultar_saldo(servicio: ServicioReportes = Depends(leer)):
    """Saldo actual: total de ingresos menos total de gastos."""
    return servicio.saldo()


@router.get("/resumen-mensual", response_model=ResumenMensual)
def resumen_mensual(
    mes: str = Query(description="Mes en formato AAAA-MM, por ejemplo 2026-11"),
    servicio: ServicioReportes = Depends(leer),
):
    """Totales del mes agrupados por categoría."""
    return servicio.resumen_mensual(mes)


@router.get("/exportar")
def exportar(
    mes: str = Query(description="Mes en formato AAAA-MM"),
    formato: str = Query(default="csv", description="csv (todos los planes) o xlsx (plan Pro)"),
    servicio: ServicioExportacion = Depends(servicio(ServicioExportacion, Permiso.EXPORTAR)),
):
    """Descarga los movimientos del mes y su resumen."""
    contenido, nombre, tipo = servicio.exportar(mes, formato)
    return Response(
        content=contenido,
        media_type=tipo,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
