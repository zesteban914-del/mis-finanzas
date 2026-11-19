"""Carga las cuentas y datos de demostración en la base de datos.

Uso:  python seed.py
La lógica está en app/datos_demo.py, para que la aplicación también pueda
cargarla al arrancar en Vercel (variable CARGAR_DATOS_DEMO).
"""

from app.datos_demo import cargar_datos

if __name__ == "__main__":
    cargar_datos()
