"""Carga datos de ejemplo: categorías, 6 meses de movimientos y presupuestos.

Uso:  python seed.py
Es idempotente: no duplica categorías ni presupuestos, y un mes que ya
tiene movimientos no se vuelve a llenar.
"""

from datetime import date
from decimal import Decimal

from app import models  # noqa: F401
from app.database import Base, SesionLocal, engine
from app.models import Categoria, Movimiento, Presupuesto, TipoMovimiento
from app.repositories.movimiento_repositorio import rango_del_mes

INGRESO, GASTO = TipoMovimiento.INGRESO, TipoMovimiento.GASTO

CATEGORIAS = [
    "Salario", "Freelance", "Vivienda", "Comida", "Transporte",
    "Servicios", "Entretenimiento", "Salud",
]

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
# Presupuestos: el del mes anterior queda superado a propósito.
PRESUPUESTOS = {0: 1_500_000, 1: 1_800_000, 2: 2_200_000}


def mes_desplazado(hoy: date, meses_atras: int) -> tuple[int, int]:
    total = hoy.year * 12 + (hoy.month - 1) - meses_atras
    return total // 12, total % 12 + 1


def obtener_o_crear_categoria(db, nombre: str) -> Categoria:
    categoria = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if categoria is None:
        categoria = Categoria(nombre=nombre)
        db.add(categoria)
        db.flush()
    return categoria


def llenar_mes(db, categorias, anio: int, mes: int, meses_atras: int, hoy: date) -> int:
    inicio, fin = rango_del_mes(anio, mes)
    ya_tiene = (
        db.query(Movimiento)
        .filter(Movimiento.fecha >= inicio, Movimiento.fecha < fin)
        .count()
    )
    if ya_tiene:
        return 0

    factor = FACTOR_POR_MES.get(meses_atras, 1.0)
    creados = 0
    for dia, tipo, monto, categoria, descripcion in PLANTILLA_MES + EXTRAS_POR_MES.get(meses_atras, []):
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
            )
        )
        creados += 1
    return creados


def cargar_datos() -> None:
    Base.metadata.create_all(bind=engine)
    db = SesionLocal()
    try:
        hoy = date.today()
        categorias = {n: obtener_o_crear_categoria(db, n) for n in CATEGORIAS}

        creados = 0
        for meses_atras in range(5, -1, -1):
            anio, mes = mes_desplazado(hoy, meses_atras)
            creados += llenar_mes(db, categorias, anio, mes, meses_atras, hoy)

        for meses_atras, limite in PRESUPUESTOS.items():
            anio, mes = mes_desplazado(hoy, meses_atras)
            clave = f"{anio:04d}-{mes:02d}"
            if db.query(Presupuesto).filter(Presupuesto.mes == clave).first() is None:
                db.add(Presupuesto(mes=clave, limite=Decimal(limite)))

        db.commit()
        print(f"Datos de ejemplo listos: {creados} movimientos nuevos.")
    finally:
        db.close()


if __name__ == "__main__":
    cargar_datos()
