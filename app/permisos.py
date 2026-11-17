"""Qué puede hacer cada usuario.

Dos ejes independientes:
- PERMISOS (acciones) dependen del rol dentro del negocio: propietario,
  empleado o contador. Una cuenta personal tiene todos.
- FUNCIONES (módulos) dependen del tipo de cuenta: personal o negocio.

Esta tabla es la única fuente de verdad: el backend la usa para permitir
o negar, y la interfaz la recibe en /auth/yo para mostrar u ocultar.
"""

import enum

from app.models.usuario import RolNegocio, TipoCuenta


class Permiso(str, enum.Enum):
    VER_MOVIMIENTOS = "VER_MOVIMIENTOS"
    REGISTRAR_MOVIMIENTOS = "REGISTRAR_MOVIMIENTOS"
    VER_REPORTES = "VER_REPORTES"            # panel, presupuestos, deudas, metas...
    EXPORTAR = "EXPORTAR"
    GESTIONAR = "GESTIONAR"                  # editar, eliminar y configurar
    GESTIONAR_EQUIPO = "GESTIONAR_EQUIPO"


class Funcion(str, enum.Enum):
    METAS = "METAS"
    CAJAS = "CAJAS"
    EQUIPO = "EQUIPO"
    COMPROBANTES = "COMPROBANTES"


TODOS_LOS_PERMISOS = frozenset(Permiso)

PERMISOS_POR_ROL_NEGOCIO = {
    RolNegocio.PROPIETARIO: TODOS_LOS_PERMISOS,
    RolNegocio.EMPLEADO: frozenset({Permiso.VER_MOVIMIENTOS, Permiso.REGISTRAR_MOVIMIENTOS}),
    RolNegocio.CONTADOR: frozenset({Permiso.VER_MOVIMIENTOS, Permiso.VER_REPORTES, Permiso.EXPORTAR}),
}

FUNCIONES_POR_TIPO = {
    TipoCuenta.PERSONAL: frozenset({Funcion.METAS}),
    TipoCuenta.NEGOCIO: frozenset({Funcion.CAJAS, Funcion.EQUIPO, Funcion.COMPROBANTES}),
}

MENSAJES_FUNCION = {
    Funcion.METAS: "Las metas de ahorro son para cuentas personales",
    Funcion.CAJAS: "Las cajas son una función de las cuentas de negocio",
    Funcion.EQUIPO: "El equipo es una función de las cuentas de negocio",
    Funcion.COMPROBANTES: "Los comprobantes son una función de las cuentas de negocio",
}


def permisos_de(usuario) -> frozenset:
    if usuario.tipo_cuenta == TipoCuenta.PERSONAL:
        return TODOS_LOS_PERMISOS - {Permiso.GESTIONAR_EQUIPO}
    return PERMISOS_POR_ROL_NEGOCIO[usuario.rol_negocio or RolNegocio.PROPIETARIO]


def funciones_de(usuario) -> frozenset:
    return FUNCIONES_POR_TIPO[usuario.tipo_cuenta]
