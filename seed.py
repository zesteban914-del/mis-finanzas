"""Carga datos de demostración para mostrar todas las funciones.

Uso:  python seed.py
Es idempotente: no duplica cuentas, categorías ni demás registros, y no
toca cuentas que no sean de demostración.

Cuentas (son de DEMOSTRACIÓN; no usar estas contraseñas en producción):
  Administrador       admin@misfinanzas.test     Admin12345
  Personal (Gratis)   demo@misfinanzas.test      Demo12345
  Negocio (Pro)       espiga@misfinanzas.test    Espiga12345
    · Empleada        laura@misfinanzas.test     Empleado12345
    · Contador        contador@misfinanzas.test  Contador12345
  Desactivada         inactiva@misfinanzas.test  Inactiva12345
"""

from datetime import date, timedelta
from decimal import Decimal

from app.catalogos import CATEGORIAS_INICIALES
from app.database import SesionLocal
from app.migraciones import preparar_base_de_datos
from app.models import (
    Caja, Categoria, Deuda, Meta, Movimiento, Plan, Presupuesto, PresupuestoCategoria, Recurrente,
    RolNegocio, RolUsuario, TipoCaja, TipoCuenta, TipoDeuda, TipoMovimiento, Transferencia, Usuario,
)
from app.models.usuario import ahora
from app.repositories.movimiento_repositorio import rango_del_mes
from app.seguridad import cifrar_contrasena

INGRESO, GASTO = TipoMovimiento.INGRESO, TipoMovimiento.GASTO
HOY = date.today()


def mes_desplazado(meses_atras: int) -> tuple[int, int]:
    total = HOY.year * 12 + (HOY.month - 1) - meses_atras
    return total // 12, total % 12 + 1


def clave_mes(meses_atras: int) -> str:
    anio, mes = mes_desplazado(meses_atras)
    return f"{anio:04d}-{mes:02d}"


# Cuentas -----------------------------------------------------------------------
def cuenta(db, email, contrasena, **datos) -> Usuario:
    """Crea la cuenta de demostración o actualiza sus datos (sin cambiar la contraseña)."""
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        usuario = Usuario(email=email, contrasena_hash=cifrar_contrasena(contrasena), acepto_terminos_en=ahora())
        db.add(usuario)
    for campo, valor in datos.items():
        setattr(usuario, campo, valor)
    db.flush()
    return usuario


def categorias_de(db, usuario, nombres) -> dict:
    resultado = {}
    for nombre in nombres:
        categoria = db.query(Categoria).filter_by(usuario_id=usuario.id, nombre=nombre).first()
        if categoria is None:
            categoria = Categoria(nombre=nombre, usuario_id=usuario.id)
            db.add(categoria)
            db.flush()
        resultado[nombre] = categoria
    return resultado


def tiene(db, modelo, usuario) -> bool:
    return db.query(modelo).filter(modelo.usuario_id == usuario.id).first() is not None


# Cuenta personal: 6 meses de historia ------------------------------------------
PLANTILLA_PERSONAL = [
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
VARIABLES = {"Comida", "Entretenimiento"}
FACTOR = {0: 1.0, 1: 1.15, 2: 0.9, 3: 1.3, 4: 1.05, 5: 0.95}
EXTRAS = {
    1: [(16, GASTO, 420_000, "Salud", "Cita odontológica")],
    2: [(15, INGRESO, 650_000, "Freelance", "Diseño de página web")],
    3: [(20, GASTO, 380_000, "Entretenimiento", "Concierto")],
    4: [(15, INGRESO, 480_000, "Freelance", "Asesoría de Excel")],
}


def llenar_mes(db, usuario, categorias, meses_atras, plantilla, factor=1.0) -> int:
    """Llena un mes de la cuenta personal, solo si ese mes aún no tiene movimientos."""
    anio, mes = mes_desplazado(meses_atras)
    inicio, fin = rango_del_mes(anio, mes)
    if db.query(Movimiento).filter(
        Movimiento.usuario_id == usuario.id, Movimiento.fecha >= inicio, Movimiento.fecha < fin
    ).count():
        return 0
    creados = 0
    for dia, tipo, monto, categoria, descripcion in plantilla:
        fecha = date(anio, mes, dia)
        if fecha > HOY:  # regla de negocio: nunca fechas futuras
            continue
        if categoria in VARIABLES:
            monto = round(monto * factor, -3)
        db.add(Movimiento(
            tipo=tipo, monto=Decimal(monto), fecha=fecha, descripcion=descripcion,
            categoria_id=categorias[categoria].id, usuario_id=usuario.id, registrado_por_id=usuario.id,
        ))
        creados += 1
    return creados


def datos_personales(db, demo) -> int:
    categorias = categorias_de(db, demo, ["Salario", "Freelance", "Vivienda", "Comida", "Transporte",
                                          "Servicios", "Entretenimiento", "Salud"])
    creados = sum(
        llenar_mes(db, demo, categorias, n, PLANTILLA_PERSONAL + EXTRAS.get(n, []), FACTOR[n])
        for n in range(5, -1, -1)
    )
    for meses_atras, limite in {0: 1_500_000, 1: 1_800_000, 2: 2_200_000}.items():
        if not db.query(Presupuesto).filter_by(usuario_id=demo.id, mes=clave_mes(meses_atras)).first():
            db.add(Presupuesto(mes=clave_mes(meses_atras), limite=Decimal(limite), usuario_id=demo.id))

    if not tiene(db, Recurrente, demo):
        ultimo = clave_mes(0)
        for dia, tipo, monto, categoria, descripcion in [
            (1, INGRESO, 3_500_000, "Salario", "Pago de nómina"),
            (3, GASTO, 950_000, "Vivienda", "Arriendo"),
            (5, GASTO, 180_000, "Servicios", "Energía, agua e internet"),
        ]:
            db.add(Recurrente(tipo=tipo, monto=Decimal(monto), descripcion=descripcion, dia_del_mes=dia,
                              categoria_id=categorias[categoria].id, activo=True, mes_inicio=clave_mes(5),
                              ultimo_mes_generado=ultimo, usuario_id=demo.id))
    if not tiene(db, PresupuestoCategoria, demo):
        db.add(PresupuestoCategoria(categoria_id=categorias["Comida"].id, limite=Decimal(450_000), usuario_id=demo.id))
        db.add(PresupuestoCategoria(categoria_id=categorias["Entretenimiento"].id, limite=Decimal(50_000), usuario_id=demo.id))
    if not tiene(db, Meta, demo):
        db.add(Meta(nombre="Viaje a Cartagena", monto_objetivo=Decimal(2_000_000), monto_ahorrado=Decimal(650_000),
                    fecha_limite=date(HOY.year + 1, 6, 30), usuario_id=demo.id))
        db.add(Meta(nombre="Fondo de emergencia", monto_objetivo=Decimal(3_000_000),
                    monto_ahorrado=Decimal(1_200_000), usuario_id=demo.id))
    if not tiene(db, Deuda, demo):
        db.add(Deuda(tipo=TipoDeuda.POR_PAGAR, contraparte="Tarjeta de crédito", descripcion="Compra del portátil",
                     monto_total=Decimal(1_800_000), monto_pagado=Decimal(600_000),
                     fecha_vencimiento=HOY + timedelta(days=12), usuario_id=demo.id))
        db.add(Deuda(tipo=TipoDeuda.POR_COBRAR, contraparte="Andrés (primo)", descripcion="Préstamo para la moto",
                     monto_total=Decimal(300_000), monto_pagado=Decimal(0),
                     fecha_vencimiento=HOY - timedelta(days=5), usuario_id=demo.id))
    return creados


# Cuenta de negocio con equipo ---------------------------------------------------
def datos_negocio(db, espiga, laura) -> int:
    categorias = categorias_de(db, espiga, CATEGORIAS_INICIALES[TipoCuenta.NEGOCIO])
    if not tiene(db, Caja, espiga):
        for nombre, tipo, saldo in [("Caja registradora", TipoCaja.EFECTIVO, 200_000),
                                    ("Bancolombia", TipoCaja.BANCO, 1_500_000),
                                    ("Nequi", TipoCaja.BILLETERA, 0)]:
            db.add(Caja(nombre=nombre, tipo=tipo, saldo_inicial=Decimal(saldo), usuario_id=espiga.id))
        db.flush()
    cajas = {c.nombre: c for c in db.query(Caja).filter_by(usuario_id=espiga.id)}

    ventas = [(d, INGRESO, 380_000 + (d % 4) * 45_000, "Ventas", "Ventas del día", "Caja registradora")
              for d in range(1, 29, 3)]
    ventas += [(d, INGRESO, 95_000, "Ventas", "Pedidos por Nequi", "Nequi") for d in (6, 14, 22)]
    gastos = [
        (2, GASTO, 1_100_000, "Arriendo del local", "Arriendo del local", "Bancolombia"),
        (4, GASTO, 640_000, "Insumos", "Harina, levadura y azúcar", "Bancolombia"),
        (11, GASTO, 210_000, "Servicios públicos", "Energía del horno", "Bancolombia"),
        (15, GASTO, 1_300_000, "Nómina", "Quincena de la cajera", "Bancolombia"),
        (18, GASTO, 520_000, "Insumos", "Mantequilla y huevos", "Caja registradora"),
    ]
    # Las ventas las registra la empleada y los gastos la propietaria. Cada
    # movimiento se crea solo si no existe ya uno con la misma fecha y descripción.
    creados = 0
    for meses_atras in (2, 1, 0):
        anio, mes = mes_desplazado(meses_atras)
        for filas, autor in ((ventas, laura), (gastos, espiga)):
            for dia, tipo, monto, categoria, descripcion, caja in filas:
                fecha = date(anio, mes, dia)
                existe = db.query(Movimiento).filter_by(usuario_id=espiga.id, fecha=fecha, descripcion=descripcion).first()
                if fecha <= HOY and not existe:
                    db.add(Movimiento(tipo=tipo, monto=Decimal(monto), fecha=fecha, descripcion=descripcion,
                                      categoria_id=categorias[categoria].id, usuario_id=espiga.id,
                                      registrado_por_id=autor.id, caja_id=cajas[caja].id))
                    creados += 1

    # Cada mes se consigna en el banco el efectivo de las ventas (con eso se pagan los gastos).
    for meses_atras in (2, 1, 0):
        anio, mes = mes_desplazado(meses_atras)
        fecha = HOY - timedelta(days=2) if meses_atras == 0 else date(anio, mes, 28)
        descripcion = f"Consignación de ventas de {fecha.strftime('%m/%Y')}"
        if not db.query(Transferencia).filter_by(usuario_id=espiga.id, descripcion=descripcion).first():
            db.add(Transferencia(origen_id=cajas["Caja registradora"].id, destino_id=cajas["Bancolombia"].id,
                                 monto=Decimal(3_300_000), fecha=fecha, descripcion=descripcion,
                                 usuario_id=espiga.id))
    if not tiene(db, Recurrente, espiga):
        for dia, monto, categoria, descripcion in [(2, 1_100_000, "Arriendo del local", "Arriendo del local"),
                                                   (15, 1_300_000, "Nómina", "Quincena de la cajera")]:
            db.add(Recurrente(tipo=GASTO, monto=Decimal(monto), descripcion=descripcion, dia_del_mes=dia,
                              categoria_id=categorias[categoria].id, caja_id=cajas["Bancolombia"].id,
                              activo=True, mes_inicio=clave_mes(2), ultimo_mes_generado=clave_mes(0),
                              usuario_id=espiga.id))
    if not tiene(db, PresupuestoCategoria, espiga):
        db.add(PresupuestoCategoria(categoria_id=categorias["Insumos"].id, limite=Decimal(1_500_000), usuario_id=espiga.id))
    if not tiene(db, Deuda, espiga):
        db.add(Deuda(tipo=TipoDeuda.POR_COBRAR, contraparte="Restaurante El Fogón", descripcion="Pedido de pan para eventos",
                     monto_total=Decimal(450_000), monto_pagado=Decimal(150_000),
                     fecha_vencimiento=HOY + timedelta(days=8), usuario_id=espiga.id))
        db.add(Deuda(tipo=TipoDeuda.POR_PAGAR, contraparte="Distribuidora Harinas S.A.S.", descripcion="Factura 1023",
                     monto_total=Decimal(1_200_000), monto_pagado=Decimal(400_000),
                     fecha_vencimiento=HOY + timedelta(days=20), usuario_id=espiga.id))
    return creados


def cargar_datos() -> None:
    preparar_base_de_datos()
    db = SesionLocal()
    try:
        admin = cuenta(db, "admin@misfinanzas.test", "Admin12345", nombre="Administrador",
                       rol=RolUsuario.ADMIN, tipo_cuenta=TipoCuenta.PERSONAL)
        demo = cuenta(db, "demo@misfinanzas.test", "Demo12345", nombre="Usuario Demo",
                      tipo_cuenta=TipoCuenta.PERSONAL, objetivo="AHORRAR", plan=Plan.GRATIS)
        if demo.solicito_pro_en is None:
            demo.solicito_pro_en = ahora()
        espiga = cuenta(db, "espiga@misfinanzas.test", "Espiga12345", nombre="Panadería La Espiga",
                        tipo_cuenta=TipoCuenta.NEGOCIO, rol_negocio=RolNegocio.PROPIETARIO, plan=Plan.PRO,
                        sector="ALIMENTOS", nit="900123456-7", responsable="Carlos Pérez")
        laura = cuenta(db, "laura@misfinanzas.test", "Empleado12345", nombre="Laura Gómez",
                       tipo_cuenta=TipoCuenta.NEGOCIO, negocio_id=espiga.id, rol_negocio=RolNegocio.EMPLEADO)
        cuenta(db, "contador@misfinanzas.test", "Contador12345", nombre="Martín Contador",
               tipo_cuenta=TipoCuenta.NEGOCIO, negocio_id=espiga.id, rol_negocio=RolNegocio.CONTADOR)
        inactiva = cuenta(db, "inactiva@misfinanzas.test", "Inactiva12345", nombre="Cuenta Inactiva",
                          activo=False, tipo_cuenta=TipoCuenta.PERSONAL)

        categorias_de(db, admin, CATEGORIAS_INICIALES[TipoCuenta.PERSONAL])
        categorias_de(db, inactiva, CATEGORIAS_INICIALES[TipoCuenta.PERSONAL])
        creados = datos_personales(db, demo) + datos_negocio(db, espiga, laura)

        db.commit()
        print(f"Datos de demostración listos: {creados} movimientos nuevos.")
    finally:
        db.close()


if __name__ == "__main__":
    cargar_datos()
