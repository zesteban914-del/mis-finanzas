"""Punto de entrada de la aplicación FastAPI."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app import config
from app import models  # noqa: F401  (registra las tablas en Base.metadata)
from app.controllers import (
    administracion,
    autenticacion,
    categorias,
    funciones,
    movimientos,
    presupuestos,
    reportes,
)
from app.database import SesionLocal, engine
from app.claves import asegurar_clave_secreta
from app.datos_demo import cargar_datos_si_vacia
from app.migraciones import preparar_base_de_datos
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    LimiteDelPlan,
    NoAutenticado,
    RecursoNoEncontrado,
    SinPermiso,
)

registro = logging.getLogger("uvicorn.error")
registro.setLevel(logging.INFO)  # en Vercel no hay uvicorn que configure este nivel


def contar_usuarios() -> int:
    db = SesionLocal()
    try:
        return db.query(models.Usuario.id).count()
    finally:
        db.close()


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Aplica las migraciones al iniciar; si la BD no responde, lo explica claramente."""
    try:
        preparar_base_de_datos()
        origen = asegurar_clave_secreta()
        registro.info("Clave de sesiones tomada de: %s", origen)
        if config.CARGAR_DATOS_DEMO and cargar_datos_si_vacia():
            registro.info("Base vacía: se cargaron las cuentas y datos de demostración.")
        registro.info("Base de datos lista: %s usuarios registrados.", contar_usuarios())
    except OperationalError as error:
        motivo = str(error.orig).strip().splitlines()[0]
        registro.error(
            "No se pudo conectar a la base de datos %s\n"
            "  Motivo: %s\n"
            "  Si usas Docker, enciende PostgreSQL con: docker compose up -d",
            engine.url.render_as_string(hide_password=True),
            motivo,
        )
        raise RuntimeError("Sin conexión a la base de datos") from None
    yield


app = FastAPI(
    lifespan=ciclo_de_vida,
    title="Mis Finanzas · Control de Gastos",
    description=(
        "API de finanzas para personas y negocios: ingresos y gastos, "
        "categorías, presupuestos (mensual y por categoría), recurrentes, "
        "metas, deudas, cajas, equipo con roles y comprobantes. Cada cuenta "
        "ve solo sus propios datos.\n\n"
        "**Para probarla aquí:** crea una cuenta en `POST /auth/registro` y "
        "luego usa el botón **Authorize** con tu correo y contraseña."
    ),
    version="3.0.0",
)

app.include_router(autenticacion.router)
app.include_router(autenticacion.planes)
app.include_router(autenticacion.equipo)
app.include_router(categorias.router)
app.include_router(movimientos.router)
app.include_router(presupuestos.router)
app.include_router(reportes.router)
app.include_router(funciones.recurrentes)
app.include_router(funciones.metas)
app.include_router(funciones.deudas)
app.include_router(funciones.cajas)
app.include_router(administracion.router)


def _crear_manejador(codigo_http: int, encabezados: dict | None = None):
    async def manejador(request: Request, exc: Exception):
        return JSONResponse(
            status_code=codigo_http,
            content={"detalle": exc.mensaje},
            headers=encabezados,
        )

    return manejador


app.add_exception_handler(ErrorDeValidacion, _crear_manejador(400))
app.add_exception_handler(
    NoAutenticado, _crear_manejador(401, {"WWW-Authenticate": "Bearer"})
)
app.add_exception_handler(LimiteDelPlan, _crear_manejador(402))
app.add_exception_handler(SinPermiso, _crear_manejador(403))
app.add_exception_handler(RecursoNoEncontrado, _crear_manejador(404))
app.add_exception_handler(ConflictoDeDatos, _crear_manejador(409))


CARPETA_INTERFAZ = Path(__file__).parent / "static"
SIN_CACHE = {"Cache-Control": "no-cache"}  # el navegador revalida: nunca usa una versión vieja


class ArchivosSinCache(StaticFiles):
    """StaticFiles con la cabecera no-cache.

    Se hace aquí y no con un middleware porque Vercel solo sirve los archivos
    desde su CDN cuando la app no tiene middlewares globales.
    """

    def file_response(self, *args, **kwargs):
        respuesta = super().file_response(*args, **kwargs)
        respuesta.headers.update(SIN_CACHE)
        return respuesta


@app.get("/", include_in_schema=False)
def interfaz_web():
    """Sirve la interfaz web; esta consume los mismos endpoints de la API."""
    return FileResponse(CARPETA_INTERFAZ / "index.html", headers=SIN_CACHE)


app.mount("/static", ArchivosSinCache(directory=CARPETA_INTERFAZ), name="static")
