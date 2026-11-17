"""Planes de suscripción: qué incluye cada uno y cuánto cuesta.

Los límites se hacen cumplir en la capa de servicios (reglas de negocio).
El cobro real se haría con una pasarela de pago (Wompi, PayU, Mercado Pago);
por ahora el usuario solicita el plan Pro y un administrador lo activa.
"""

from app.models.usuario import Plan, TipoCuenta

LIMITES = {
    Plan.GRATIS: {
        "recurrentes": 3,
        "metas": 2,
        "cajas": 2,
        "miembros": 1,
        "exportar_excel": False,
        "comprobantes": False,
    },
    Plan.PRO: {
        "recurrentes": 50,
        "metas": 20,
        "cajas": 20,
        "miembros": 10,
        "exportar_excel": True,
        "comprobantes": True,
    },
}

# Precio mensual en pesos colombianos (referencia; se debe validar con clientes).
PRECIOS = {
    (TipoCuenta.PERSONAL, Plan.GRATIS): 0,
    (TipoCuenta.PERSONAL, Plan.PRO): 9_900,
    (TipoCuenta.NEGOCIO, Plan.GRATIS): 0,
    (TipoCuenta.NEGOCIO, Plan.PRO): 39_900,
}

NOMBRES_RECURSOS = {
    "recurrentes": "movimientos recurrentes",
    "metas": "metas de ahorro",
    "cajas": "cajas",
    "miembros": "miembros en tu equipo",
}

MENSAJES_CARACTERISTICAS = {
    "exportar_excel": "Exportar a Excel es una función del plan Pro. En el plan Gratis puedes exportar a CSV.",
    "comprobantes": "Adjuntar comprobantes es una función del plan Pro.",
}


def beneficios(tipo: TipoCuenta, plan: Plan) -> list:
    """Lista legible de lo que incluye un plan para un tipo de cuenta."""
    limites = LIMITES[plan]
    lista = [
        "Movimientos, categorías y presupuestos ilimitados",
        f"Hasta {limites['recurrentes']} movimientos recurrentes",
        "Exportar a CSV" + (" y Excel" if limites["exportar_excel"] else ""),
    ]
    if tipo == TipoCuenta.PERSONAL:
        lista.append(f"Hasta {limites['metas']} metas de ahorro")
    else:
        lista.append(f"Hasta {limites['cajas']} cajas o cuentas")
        lista.append(f"Hasta {limites['miembros']} miembros en tu equipo")
        if limites["comprobantes"]:
            lista.append("Comprobantes adjuntos (fotos o PDF)")
    return lista
