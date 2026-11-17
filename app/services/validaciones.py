"""Validaciones compartidas entre servicios."""

import re
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from app.services.excepciones import ErrorDeValidacion

PATRON_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_NIT = re.compile(r"^\d{5,15}(-\d)?$")


def validar_mes(mes: str) -> Tuple[int, int]:
    """Valida el formato AAAA-MM y devuelve (año, mes) como enteros."""
    if not mes or not PATRON_MES.match(mes):
        raise ErrorDeValidacion(
            "El mes debe tener el formato AAAA-MM, por ejemplo 2026-01"
        )
    anio, numero_mes = mes.split("-")
    return int(anio), int(numero_mes)


def mes_de(fecha: date) -> str:
    return f"{fecha.year:04d}-{fecha.month:02d}"


def mes_siguiente(mes: str) -> str:
    anio, numero = validar_mes(mes)
    return f"{anio + 1:04d}-01" if numero == 12 else f"{anio:04d}-{numero + 1:02d}"


def validar_positivo(valor: Optional[Decimal], mensaje: str) -> None:
    if valor is None or valor <= 0:
        raise ErrorDeValidacion(mensaje)


def validar_no_futura(fecha: date, mensaje: str = "La fecha no puede ser futura") -> None:
    if fecha > date.today():
        raise ErrorDeValidacion(mensaje)


def texto_obligatorio(valor: Optional[str], campo: str) -> str:
    limpio = (valor or "").strip()
    if not limpio:
        raise ErrorDeValidacion(f"El campo «{campo}» es obligatorio")
    return limpio


def validar_email(email: str) -> str:
    limpio = (email or "").strip().lower()
    if not PATRON_EMAIL.match(limpio):
        raise ErrorDeValidacion("El correo electrónico no es válido")
    return limpio


def validar_contrasena(contrasena: str) -> None:
    """Regla: mínimo 8 caracteres, con al menos una letra y un número."""
    if (
        len(contrasena) < 8
        or not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]", contrasena)
        or not re.search(r"\d", contrasena)
    ):
        raise ErrorDeValidacion(
            "La contraseña debe tener al menos 8 caracteres e incluir letras y números"
        )


def validar_opcion(valor: Optional[str], opciones: dict, campo: str) -> Optional[str]:
    if not valor:
        return None
    if valor not in opciones:
        raise ErrorDeValidacion(f"El valor de «{campo}» no es válido")
    return valor


def validar_nit(nit: Optional[str]) -> Optional[str]:
    limpio = (nit or "").strip().replace(".", "").replace(" ", "")
    if not limpio:
        return None
    if not PATRON_NIT.match(limpio):
        raise ErrorDeValidacion("El NIT debe tener solo números, por ejemplo 900123456-7")
    return limpio
