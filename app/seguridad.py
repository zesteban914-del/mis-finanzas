"""Cifrado de contraseñas y tokens de sesión (JWT)."""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from functools import cache
from typing import Optional

import jwt

from app import config

ALGORITMO_HASH = "pbkdf2_sha256"


def cifrar_contrasena(contrasena: str) -> str:
    """Devuelve 'algoritmo$iteraciones$sal$resumen'. Nunca se guarda la contraseña."""
    sal = secrets.token_bytes(16)
    resumen = hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode(), sal, config.ITERACIONES_HASH
    )
    return "$".join(
        [
            ALGORITMO_HASH,
            str(config.ITERACIONES_HASH),
            base64.b64encode(sal).decode(),
            base64.b64encode(resumen).decode(),
        ]
    )


def verificar_contrasena(contrasena: str, guardada: str) -> bool:
    try:
        algoritmo, iteraciones, sal, resumen = guardada.split("$")
    except ValueError:
        return False
    if algoritmo != ALGORITMO_HASH:
        return False
    calculado = hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode(), base64.b64decode(sal), int(iteraciones)
    )
    # compare_digest tarda lo mismo acierte o no: no revela pistas por tiempo.
    return hmac.compare_digest(calculado, base64.b64decode(resumen))


@cache
def hash_ficticio() -> str:
    """Se compara contra este hash cuando el correo no existe, para que el
    tiempo de respuesta no revele qué correos están registrados."""
    return cifrar_contrasena(secrets.token_hex(16))


def crear_token(usuario_id: int) -> str:
    ahora = datetime.now(timezone.utc)
    datos = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=config.MINUTOS_EXPIRACION_TOKEN),
    }
    return jwt.encode(datos, config.CLAVE_SECRETA, algorithm=config.ALGORITMO_TOKEN)


def leer_token(token: str) -> Optional[int]:
    """Devuelve el id del usuario, o None si el token es inválido o expiró."""
    try:
        datos = jwt.decode(
            token, config.CLAVE_SECRETA, algorithms=[config.ALGORITMO_TOKEN]
        )
        return int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
