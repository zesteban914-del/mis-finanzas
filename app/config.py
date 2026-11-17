"""Configuración de la aplicación, leída de variables de entorno.

Los valores por defecto sirven para desarrollo. En producción se debe
definir al menos CLAVE_SECRETA con un valor largo y aleatorio.
"""

import os

CLAVE_DE_DESARROLLO = "solo-para-desarrollo-cambiar-en-produccion"

# Firma los tokens de sesión: quien la conozca podría falsificar sesiones.
CLAVE_SECRETA = os.getenv("CLAVE_SECRETA", CLAVE_DE_DESARROLLO)
ALGORITMO_TOKEN = "HS256"
MINUTOS_EXPIRACION_TOKEN = int(os.getenv("MINUTOS_EXPIRACION_TOKEN", "480"))

# Iteraciones de PBKDF2 para cifrar contraseñas (valor recomendado por OWASP).
# Las pruebas usan un valor bajo para correr rápido.
ITERACIONES_HASH = int(os.getenv("ITERACIONES_HASH", "600000"))
