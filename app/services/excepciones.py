"""Excepciones de negocio.

Los servicios lanzan estas excepciones y la aplicación (main.py) las
traduce a códigos HTTP: 400, 404 y 409. Así la capa de negocio no
depende de FastAPI y se puede probar de forma aislada.
"""


class ErrorDeAplicacion(Exception):
    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(mensaje)


class ErrorDeValidacion(ErrorDeAplicacion):
    """Datos inválidos según las reglas de negocio → HTTP 400."""


class RecursoNoEncontrado(ErrorDeAplicacion):
    """El recurso solicitado no existe → HTTP 404."""


class ConflictoDeDatos(ErrorDeAplicacion):
    """La operación choca con el estado actual de los datos → HTTP 409."""
