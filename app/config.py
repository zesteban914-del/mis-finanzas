"""Configuración de la aplicación, leída de variables de entorno.

Los valores por defecto sirven para desarrollo. En producción se debe
definir al menos CLAVE_SECRETA con un valor largo y aleatorio.
"""

import os

CLAVE_DE_DESARROLLO = "solo-para-desarrollo-cambiar-en-produccion"

# Firma los tokens de sesión: quien la conozca podría falsificar sesiones.
# Al arrancar, app/claves.py la reemplaza por la variable CLAVE_SECRETA o, si
# no existe, por una clave aleatoria guardada en la base de datos. Este valor
# solo se usa en scripts que no arrancan la aplicación.
CLAVE_SECRETA = os.getenv("CLAVE_SECRETA", CLAVE_DE_DESARROLLO)
ALGORITMO_TOKEN = "HS256"
MINUTOS_EXPIRACION_TOKEN = int(os.getenv("MINUTOS_EXPIRACION_TOKEN", "480"))

# Iteraciones de PBKDF2 para cifrar contraseñas (valor recomendado por OWASP).
# Las pruebas usan un valor bajo para correr rápido.
ITERACIONES_HASH = int(os.getenv("ITERACIONES_HASH", "600000"))

# Vercel define la variable VERCEL en sus servidores.
EN_VERCEL = bool(os.getenv("VERCEL"))

# Si está activa y la base no tiene usuarios, al arrancar se cargan las cuentas
# y datos de demostración (útil en Vercel, donde no se puede ejecutar seed.py).
CARGAR_DATOS_DEMO = os.getenv("CARGAR_DATOS_DEMO", "").strip().lower() in {"1", "true", "si", "sí"}
