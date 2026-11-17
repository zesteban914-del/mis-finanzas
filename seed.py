"""Carga datos de demostración: cuentas, categorías, 6 meses de movimientos y presupuestos.

Uso:  python seed.py
Es idempotente: no duplica cuentas, categorías ni presupuestos, y un mes que
ya tiene movimientos no se vuelve a llenar.

Cuentas que crea (las contraseñas se pueden cambiar con variables de entorno):
  - Administrador:  admin@misfinanzas.test  / Admin12345   (SEED_ADMIN_CONTRASENA)
  - Usuario demo:   demo@misfinanzas.test   / Demo12345    (SEED_DEMO_CONTRASENA)
  - Dos cuentas extra para que la sección de administración tenga contenido.
Son cuentas de DEMOSTRACIÓN: no usar estas contraseñas en producción.
"""

import os
from datetime import date
from decimal import Decimal

from app import models  # noqa: F401
from app.database import Base, SesionLocal, engine
from app.models import Categoria, Movimiento, Presupuesto, RolUsuario, TipoMovimiento, Usuario
from app.repositories.movimiento_repositorio import rango_del_mes
from app.seguridad import cifrar_contrasena
from app.services.autenticacion_servicio import CATEGORIAS_INICIALES

INGRESO, GASTO = TipoMovimiento.INGRESO, TipoMovimiento.GASTO

CUENTAS = [
    # (nombre, email, contraseña, rol, activo)
    ("Administrador", "admin@misfinanzas.test", os.getenv("SEED_ADMIN_CONTRASENA", "Admin12345"), RolUsuario.ADMIN, True),
    ("Usuario Demo", "demo@misfinanzas.test", os.getenv("SEED_DEMO_CONTRASENA", "Demo12345"), RolUsuario.USUARIO, True),
    ("Panadería La Espiga", "espiga@misfinanzas.test", "Espiga12345", RolUsuario.USUARIO, True),
    ("Cuenta Inactiva", "inactiva@misfinanzas.test", "Inactiva12345", RolUsuario.USUARIO, False),
]

CATEGORIAS_DEMO = ["Salario", "Freelance", "Vivienda", "Comida", "Transporte", "Servicios", "Entretenimiento", "Salud"]

# (día, tipo, monto, categoría, descripción). Los montos de los gastos
# variables se multiplican por un factor distinto cada mes.
PLANTILLA_MES = [
    (1, INGRESO, 3_500_000, "Salario", "Pago de nómina"),
    (3, GASTO, 950_000, "Vivienda", "Arriendo"),
    (5, GASTO, 180_000, "Servicios", "Energía, agua e internet"),
    (7, GASTO, 135_000, "Comida", "Mercado quincenal"),
    (10, GASTO, 95_000, "Transporte", "Recarga tarjeta de transporte"),
    (13, GASTO, 72_000, "Entretenimiento", "Salida a cine"),
    (18, GASTO, 64_000, "Salud", "Farmacia"),
    (21, GASTO, 128_000, "Comida", "Mercado quincenal"),
    (25, GASTO, 48_000, "Comida", "Restaurante"),
]
CATEGORIAS_VARIABLES = {"Comida", "Entretenimiento"}

# Ajustes por mes (0 = mes actual, 1 = mes anterior, ...).
FACTOR_POR_MES = {0: 1.0, 1: 1.15, 2: 0.9, 3: 1.3, 4: 1.05, 5: 0.95}
EXTRAS_POR_MES = {
    1: [(16, GASTO, 420_000, "Salud", "Cita odontológica")],
    2: [(15, INGRESO, 650_000, "Freelance", "Diseño de página web")],
    3: [(20, GASTO, 380_000, "Entretenimiento", "Concierto")],
    4: [(15, INGRESO, 480_000, "Freelance", "Asesoría de Excel")],
}
# Presupuestos del usuario demo: el del mes anterior queda superado a propósito.
PRESUPUESTOS = {0: 1_500_000, 1: 1_800_000, 2: 2_200_000}

# Pocos movimientos para la cuenta de la panadería (un negocio).
MOVIMIENTOS_NEGOCIO = [
    (2, INGRESO, 1_250_000, "Ventas", "Ventas de la semana"),
    (4, GASTO, 380_000, "Insumos", "Harina y levadura"),
    (6, GASTO, 210_000, "Servicios", "Energía del horno"),
]


def mes_desplazado(hoy: date, meses_atras: int) -> tuple[int, int]:
    total = hoy.year * 12 + (hoy.month - 1) - meses_atras
    return total // 12, total % 12 + 1


def obtener_o_crear_usuario(db, nombre, email, contrasena, rol, activo) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        usuario = Usuario(
            nombre=nombre, email=email, contrasena_hash=cifrar_contrasena(contrasena),
            rol=rol, activo=activo,
        )
        db.add(usuario)
        db.flush()
    return usuario


def categorias_de(db, usuario: Usuario, nombres) -> dict:
    resultado = {}
    for nombre in nombres:
        categoria = (
            db.query(Categoria)
            .filter(Categoria.usuario_id == usuario.id, Categoria.nombre == nombre)
            .first()
        )
        if categoria is None:
            categoria = Categoria(nombre=nombre, usuario_id=usuario.id)
            db.add(categoria)
            db.flush()
        resultado[nombre] = categoria
    return resultado


def llenar_mes(db, usuario, categorias, anio, mes, plantilla, factor, hoy) -> int:
    inicio, fin = rango_del_mes(anio, mes)
    ya_tiene = (
        db.query(Movimiento)
        .filter(
            Movimiento.usuario_id == usuario.id,
            Movimiento.fecha >= inicio,
            Movimiento.fecha < fin,
        )
        .count()
    )
    if ya_tiene:
        return 0

    creados = 0
    for dia, tipo, monto, categoria, descripcion in plantilla:
        fecha = date(anio, mes, dia)
        if fecha > hoy:  # regla de negocio: nunca fechas futuras
            continue
        if categoria in CATEGORIAS_VARIABLES:
            monto = round(monto * factor, -3)
        db.add(
            Movimiento(
                tipo=tipo,
                monto=Decimal(monto),
                fecha=fecha,
                descripcion=descripcion,
                categoria_id=categorias[categoria].id,
                usuario_id=usuario.id,
            )
        )
        creados += 1
    return creados


def cargar_datos() -> None:
    Base.metadata.create_all(bind=engine)
    db = SesionLocal()
    try:
        hoy = date.today()
        usuarios = {cuenta[1]: obtener_o_crear_usuario(db, *cuenta) for cuenta in CUENTAS}
        admin = usuarios["admin@misfinanzas.test"]
        demo = usuarios["demo@misfinanzas.test"]
        negocio = usuarios["espiga@misfinanzas.test"]
        inactiva = usuarios["inactiva@misfinanzas.test"]

        categorias_de(db, admin, CATEGORIAS_INICIALES)
        categorias_de(db, inactiva, CATEGORIAS_INICIALES)

        # Usuario demo: 6 meses de historia y 3 presupuestos.
        categorias_demo = categorias_de(db, demo, CATEGORIAS_DEMO)
        creados = 0
        for meses_atras in range(5, -1, -1):
            anio, mes = mes_desplazado(hoy, meses_atras)
            plantilla = PLANTILLA_MES + EXTRAS_POR_MES.get(meses_atras, [])
            factor = FACTOR_POR_MES.get(meses_atras, 1.0)
            creados += llenar_mes(db, demo, categorias_demo, anio, mes, plantilla, factor, hoy)

        for meses_atras, limite in PRESUPUESTOS.items():
            anio, mes = mes_desplazado(hoy, meses_atras)
            clave = f"{anio:04d}-{mes:02d}"
            existe = (
                db.query(Presupuesto)
                .filter(Presupuesto.usuario_id == demo.id, Presupuesto.mes == clave)
                .first()
            )
            if existe is None:
                db.add(Presupuesto(mes=clave, limite=Decimal(limite), usuario_id=demo.id))

        # Cuenta de negocio: unos pocos movimientos del mes actual.
        categorias_negocio = categorias_de(db, negocio, ["Ventas", "Insumos", "Servicios"])
        creados += llenar_mes(
            db, negocio, categorias_negocio, hoy.year, hoy.month, MOVIMIENTOS_NEGOCIO, 1.0, hoy
        )

        db.commit()
        print(f"Datos de demostración listos: {len(CUENTAS)} cuentas, {creados} movimientos nuevos.")
    finally:
        db.close()


if __name__ == "__main__":
    cargar_datos()
