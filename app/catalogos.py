"""Opciones fijas que la interfaz muestra en los formularios."""

from app.models.usuario import TipoCuenta

OBJETIVOS_PERSONALES = {
    "CONTROLAR_GASTOS": "Saber en qué se me va el dinero",
    "AHORRAR": "Ahorrar para una meta",
    "SALIR_DE_DEUDAS": "Salir de deudas",
    "ORGANIZAR": "Organizar mis finanzas del mes",
}

SECTORES_NEGOCIO = {
    "COMERCIO": "Comercio o tienda",
    "ALIMENTOS": "Restaurante, panadería o alimentos",
    "SERVICIOS": "Servicios profesionales",
    "MANUFACTURA": "Producción o manufactura",
    "OTRO": "Otro",
}

CATEGORIAS_INICIALES = {
    TipoCuenta.PERSONAL: [
        "Salario", "Comida", "Transporte", "Vivienda",
        "Servicios", "Salud", "Entretenimiento", "Educación",
    ],
    TipoCuenta.NEGOCIO: [
        "Ventas", "Servicios prestados", "Insumos", "Nómina",
        "Arriendo del local", "Servicios públicos", "Impuestos", "Publicidad", "Transporte",
    ],
}
