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
    movimientos,
    presupuestos,
    reportes,
)
from app.database import Base, engine
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    NoAutenticado,
    RecursoNoEncontrado,
    SinPermiso,
)

registro = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Crea las tablas al iniciar; si la BD no responde, lo explica claramente."""
    if config.CLAVE_SECRETA == config.CLAVE_DE_DESARROLLO:
        registro.warning(
            "Usando la clave de desarrollo para firmar sesiones. "
            "En producción define la variable de entorno CLAVE_SECRETA."
        )
    try:
        Base.metadata.create_all(bind=engine)
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
        "API para registrar ingresos y gastos, administrar categorías, "
        "consultar el saldo, generar resúmenes mensuales y controlar "
        "presupuestos. Cada usuario ve solo sus propios datos.\n\n"
        "**Para probarla aquí:** crea una cuenta en `POST /auth/registro` y "
        "luego usa el botón **Authorize** con tu correo y contraseña."
    ),
    version="2.0.0",
)

app.include_router(autenticacion.router)
app.include_router(categorias.router)
app.include_router(movimientos.router)
app.include_router(presupuestos.router)
app.include_router(reportes.router)
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
app.add_exception_handler(SinPermiso, _crear_manejador(403))
app.add_exception_handler(RecursoNoEncontrado, _crear_manejador(404))
app.add_exception_handler(ConflictoDeDatos, _crear_manejador(409))


CARPETA_INTERFAZ = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=CARPETA_INTERFAZ), name="static")


@app.middleware("http")
async def revalidar_interfaz(request: Request, call_next):
    """Evita que el navegador use una versión vieja de la interfaz tras un cambio."""
    respuesta = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


@app.get("/", include_in_schema=False)
def interfaz_web():
    """Sirve la interfaz web; esta consume los mismos endpoints de la API."""
    return FileResponse(CARPETA_INTERFAZ / "index.html")
