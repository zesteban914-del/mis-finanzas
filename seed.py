"""Carga datos de ejemplo: categorías, movimientos y un presupuesto.

Uso:  python seed.py
Es idempotente: si una categoría o presupuesto ya existe, no lo duplica.
"""

from datetime import date, timedelta
from decimal import Decimal

from app import models  # noqa: F401
from app.database import Base, SesionLocal, engine
from app.models import Categoria, Movimiento, Presupuesto, TipoMovimiento

CATEGORIAS = ["Salario", "Comida", "Transporte", "Servicios", "Entretenimiento"]


def obtener_o_crear_categoria(db, nombre: str) -> Categoria:
    categoria = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if categoria is None:
        categoria = Categoria(nombre=nombre)
        db.add(categoria)
        db.flush()
    return categoria


def cargar_datos() -> None:
    Base.metadata.create_all(bind=engine)
    db = SesionLocal()
    try:
        categorias = {n: obtener_o_crear_categoria(db, n) for n in CATEGORIAS}

        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        mes_actual = inicio_mes.strftime("%Y-%m")

        if db.query(Movimiento).count() == 0:
            ejemplos = [
                (TipoMovimiento.INGRESO, "3500000", 0, "Salario", "Pago de nómina"),
                (TipoMovimiento.GASTO, "120000", 1, "Comida", "Mercado semanal"),
                (TipoMovimiento.GASTO, "45000", 2, "Transporte", "Recarga tarjeta"),
                (TipoMovimiento.GASTO, "180000", 3, "Servicios", "Energía y agua"),
                (TipoMovimiento.GASTO, "60000", 4, "Entretenimiento", "Cine"),
                (TipoMovimiento.GASTO, "35000", 5, "Comida", "Almuerzo"),
            ]
            for tipo, monto, dias, categoria, descripcion in ejemplos:
                # Nunca una fecha futura, ni anterior al inicio del mes actual.
                fecha = min(inicio_mes + timedelta(days=dias), hoy)
                db.add(
                    Movimiento(
                        tipo=tipo,
                        monto=Decimal(monto),
                        fecha=fecha,
                        descripcion=descripcion,
                        categoria_id=categorias[categoria].id,
                    )
                )

        if db.query(Presupuesto).filter(Presupuesto.mes == mes_actual).first() is None:
            db.add(Presupuesto(mes=mes_actual, limite=Decimal("1500000")))

        db.commit()
        print(f"Datos de ejemplo cargados (presupuesto para {mes_actual}).")
    finally:
        db.close()


if __name__ == "__main__":
    cargar_datos()
