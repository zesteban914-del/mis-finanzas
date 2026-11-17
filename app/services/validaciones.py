"""Validaciones compartidas entre servicios."""

import re
from typing import Tuple

from app.services.excepciones import ErrorDeValidacion

PATRON_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validar_mes(mes: str) -> Tuple[int, int]:
    """Valida el formato AAAA-MM y devuelve (año, mes) como enteros."""
    if not mes or not PATRON_MES.match(mes):
        raise ErrorDeValidacion(
            "El mes debe tener el formato AAAA-MM, por ejemplo 2026-01"
        )
    anio, numero_mes = mes.split("-")
    return int(anio), int(numero_mes)
