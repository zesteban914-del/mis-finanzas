"""Hace cumplir los permisos (app/permisos.py) y los límites del plan (app/planes.py)."""

from app.models import Plan
from app.permisos import MENSAJES_FUNCION, Funcion, Permiso, funciones_de, permisos_de
from app.planes import LIMITES, MENSAJES_CARACTERISTICAS, NOMBRES_RECURSOS
from app.services.excepciones import LimiteDelPlan, SinPermiso


def exigir_permiso(usuario, permiso: Permiso) -> None:
    if permiso not in permisos_de(usuario):
        raise SinPermiso("Tu rol en el negocio no permite realizar esta acción")


def exigir_funcion(usuario, funcion: Funcion) -> None:
    if funcion not in funciones_de(usuario):
        raise SinPermiso(MENSAJES_FUNCION[funcion])


def exigir_cupo(plan: Plan, recurso: str, cantidad_actual: int) -> None:
    """Ej.: el plan Gratis permite hasta 3 recurrentes; el cuarto se rechaza."""
    limite = LIMITES[plan][recurso]
    if cantidad_actual >= limite:
        raise LimiteDelPlan(
            f"Tu plan {plan.value.capitalize()} permite hasta {limite} "
            f"{NOMBRES_RECURSOS[recurso]}. Mejora a Pro para tener más."
        )


def exigir_caracteristica(plan: Plan, caracteristica: str) -> None:
    if not LIMITES[plan][caracteristica]:
        raise LimiteDelPlan(MENSAJES_CARACTERISTICAS[caracteristica])
