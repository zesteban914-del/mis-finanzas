"""Excepciones de negocio.

Los servicios lanzan estas excepciones y la aplicación (main.py) las
traduce a códigos HTTP: 400, 401, 403, 404 y 409. Así la capa de negocio
no depende de FastAPI y se puede probar de forma aislada.
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


class NoAutenticado(ErrorDeAplicacion):
    """Falta iniciar sesión, o la sesión no es válida → HTTP 401."""


class SinPermiso(ErrorDeAplicacion):
    """La sesión es válida pero no alcanza para esta acción → HTTP 403."""
