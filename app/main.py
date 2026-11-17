"""Punto de entrada de la aplicación FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  (registra las tablas en Base.metadata)
from app.controllers import categorias, movimientos, presupuestos, reportes
from app.database import Base, engine
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    RecursoNoEncontrado,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
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
