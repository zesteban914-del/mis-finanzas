"""Clave que firma las sesiones (JWT).

Si se define la variable de entorno CLAVE_SECRETA, se usa esa. Si no, la
aplicación genera una clave aleatoria la primera vez que arranca, la guarda
en la base de datos y la reutiliza en cada inicio: nadie tiene que escribirla
ni copiarla, y las sesiones siguen siendo válidas tras reiniciar o desplegar.
"""

import os
import secrets

from sqlalchemy.exc import IntegrityError

from app import config
from app.database import SesionLocal
from app.models import Configuracion

NOMBRE = "clave_secreta"


def asegurar_clave_secreta() -> str:
    """Deja en config.CLAVE_SECRETA la clave definitiva y dice de dónde salió."""
    if os.getenv("CLAVE_SECRETA"):
        config.CLAVE_SECRETA = os.environ["CLAVE_SECRETA"]
        return "variable de entorno"

    db = SesionLocal()
    try:
        fila = db.get(Configuracion, NOMBRE)
        if fila is None:
            db.add(Configuracion(clave=NOMBRE, valor=secrets.token_urlsafe(48)))
            try:
                db.commit()
            except IntegrityError:
                # Otra instancia la creó al mismo tiempo: se usa la suya.
                db.rollback()
            fila = db.get(Configuracion, NOMBRE)
        config.CLAVE_SECRETA = fila.valor
        return "base de datos"
    finally:
        db.close()
