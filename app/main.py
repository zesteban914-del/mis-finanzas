"""Punto de entrada de la aplicación FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app import models  # noqa: F401  (registra las tablas en Base.metadata)
from app.controllers import categorias, movimientos, presupuestos, reportes
from app.database import Base, engine
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    RecursoNoEncontrado,
)

registro = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Crea las tablas al iniciar; si la BD no responde, lo explica claramente."""
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
    title="Control de Gastos Personales",
    description=(
        "API para registrar ingresos y gastos, administrar categorías, "
        "consultar el saldo, generar resúmenes mensuales y controlar "
        "presupuestos."
    ),
    version="1.0.0",
)

app.include_router(categorias.router)
app.include_router(movimientos.router)
app.include_router(presupuestos.router)
app.include_router(reportes.router)


def _crear_manejador(codigo_http: int):
    async def manejador(request: Request, exc: Exception):
        return JSONResponse(
            status_code=codigo_http, content={"detalle": exc.mensaje}
        )

    return manejador


app.add_exception_handler(ErrorDeValidacion, _crear_manejador(400))
app.add_exception_handler(RecursoNoEncontrado, _crear_manejador(404))
app.add_exception_handler(ConflictoDeDatos, _crear_manejador(409))


@app.get("/", tags=["Inicio"])
def inicio():
    return {
        "mensaje": "API de Control de Gastos Personales",
        "documentacion": "/docs",
    }
