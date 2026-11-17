"""Plan de suscripción y equipo de trabajo de una cuenta."""

from typing import List

from sqlalchemy.orm import Session

from app.models import Plan, RolNegocio, TipoCuenta, Usuario
from app.models.usuario import ahora
from app.planes import PRECIOS, beneficios
from app.repositories import RepositorioMovimientos, RepositorioUsuarios
from app.schemas import MiembroActualizar, MiembroCrear, PlanInfo
from app.seguridad import cifrar_contrasena
from app.services.autorizacion import exigir_cupo
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    RecursoNoEncontrado,
    SinPermiso,
)
from app.services.validaciones import texto_obligatorio, validar_contrasena, validar_email


class ServicioPlanes:
    def __init__(self, db: Session, usuario: Usuario):
        self.usuario = usuario
        self.repositorio = RepositorioUsuarios(db)

    def catalogo(self) -> List[PlanInfo]:
        tipo = self.usuario.tipo_cuenta
        return [
            PlanInfo(
                plan=plan,
                precio_mensual=PRECIOS[(tipo, plan)],
                beneficios=beneficios(tipo, plan),
                actual=plan == self.usuario.plan_efectivo,
            )
            for plan in Plan
        ]

    def solicitar_pro(self) -> Usuario:
        """Sin pasarela de pago aún: queda la solicitud y un administrador la activa."""
        if self.usuario.negocio_id:
            raise SinPermiso("Solo el propietario del negocio puede cambiar el plan")
        if self.usuario.plan == Plan.PRO:
            raise ErrorDeValidacion("Ya tienes el plan Pro")
        if self.usuario.solicito_pro_en is None:
            self.repositorio.actualizar(self.usuario, solicito_pro_en=ahora())
        return self.usuario


class ServicioEquipo:
    """El propietario de un negocio agrega empleados y contadores a su cuenta."""

    ROLES_PERMITIDOS = {RolNegocio.EMPLEADO, RolNegocio.CONTADOR}

    def __init__(self, db: Session, propietario: Usuario):
        self.propietario = propietario
        self.repositorio = RepositorioUsuarios(db)
        self.repositorio_movimientos = RepositorioMovimientos(db, propietario.id)

    def listar(self) -> List[Usuario]:
        return self.repositorio.listar_miembros(self.propietario.id)

    def agregar(self, datos: MiembroCrear) -> Usuario:
        nombre = texto_obligatorio(datos.nombre, "nombre")
        email = validar_email(datos.email)
        validar_contrasena(datos.contrasena)
        self._validar_rol(datos.rol_negocio)
        if self.repositorio.obtener_por_email(email) is not None:
            raise ConflictoDeDatos("Ya existe una cuenta registrada con ese correo")
        exigir_cupo(self.propietario.plan, "miembros", len(self.listar()))
        return self.repositorio.crear(
            nombre=nombre,
            email=email,
            contrasena_hash=cifrar_contrasena(datos.contrasena),
            tipo_cuenta=TipoCuenta.NEGOCIO,
            negocio_id=self.propietario.id,
            rol_negocio=datos.rol_negocio,
        )

    def actualizar(self, miembro_id: int, datos: MiembroActualizar) -> Usuario:
        miembro = self._obtener(miembro_id)
        cambios = datos.model_dump(exclude_none=True)
        if "rol_negocio" in cambios:
            self._validar_rol(cambios["rol_negocio"])
        return self.repositorio.actualizar(miembro, **cambios)

    def eliminar(self, miembro_id: int) -> None:
        miembro = self._obtener(miembro_id)
        self.repositorio_movimientos.quitar_autor(miembro.id)
        self.repositorio.eliminar(miembro)

    def _obtener(self, miembro_id: int) -> Usuario:
        miembro = self.repositorio.obtener_por_id(miembro_id)
        if miembro is None or miembro.negocio_id != self.propietario.id:
            raise RecursoNoEncontrado(f"El miembro con id {miembro_id} no existe")
        return miembro

    def _validar_rol(self, rol: RolNegocio) -> None:
        if rol not in self.ROLES_PERMITIDOS:
            raise ErrorDeValidacion("El rol de un miembro debe ser Empleado o Contador")
