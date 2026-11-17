from typing import List

from sqlalchemy.orm import Session

from app.models import Plan, RolUsuario, TipoCuenta, Usuario
from app.repositories import RepositorioUsuarios
from app.schemas import (
    CambioUsuarioAdmin,
    EstadisticasAdmin,
    UsuarioAdminRespuesta,
    UsuarioRespuesta,
)
from app.services.excepciones import ErrorDeValidacion, RecursoNoEncontrado


class ServicioAdministracion:
    """Gestión de cuentas por parte de un administrador de la plataforma.

    Por privacidad, el administrador ve datos de las cuentas y cuántos
    movimientos tiene cada una, pero nunca montos ni descripciones.
    """

    def __init__(self, db: Session, administrador: Usuario):
        self.repositorio = RepositorioUsuarios(db)
        self.administrador = administrador

    def listar_usuarios(self) -> List[UsuarioAdminRespuesta]:
        return [
            UsuarioAdminRespuesta(
                **UsuarioRespuesta.model_validate(usuario).model_dump(),
                movimientos_registrados=cantidad,
            )
            for usuario, cantidad in self.repositorio.listar_con_cantidad_de_movimientos()
        ]

    def estadisticas(self) -> EstadisticasAdmin:
        r = self.repositorio
        return EstadisticasAdmin(
            total_usuarios=r.contar(),
            usuarios_activos=r.contar(activo=True),
            administradores=r.contar(rol=RolUsuario.ADMIN),
            movimientos_registrados=r.contar_movimientos(),
            cuentas_personales=r.contar_titulares(tipo_cuenta=TipoCuenta.PERSONAL),
            cuentas_negocio=r.contar_titulares(tipo_cuenta=TipoCuenta.NEGOCIO),
            cuentas_pro=r.contar_titulares(plan=Plan.PRO),
            solicitudes_pro=r.contar(Usuario.solicito_pro_en.isnot(None), plan=Plan.GRATIS),
            ingreso_mensual_estimado=r.ingreso_mensual_estimado(),
        )

    def actualizar_usuario(self, usuario_id: int, cambios: CambioUsuarioAdmin) -> Usuario:
        usuario = self.repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise RecursoNoEncontrado(f"El usuario con id {usuario_id} no existe")

        datos = cambios.model_dump(exclude_none=True)
        if usuario.id == self.administrador.id and (
            datos.get("activo") is False or datos.get("rol") == RolUsuario.USUARIO
        ):
            raise ErrorDeValidacion(
                "No puedes desactivar tu propia cuenta ni quitarte el rol de administrador"
            )
        if "plan" in datos:
            if usuario.negocio_id:
                raise ErrorDeValidacion(
                    "Los miembros de un equipo usan el plan del negocio; cámbialo en la cuenta del propietario"
                )
            datos["solicito_pro_en"] = None  # la solicitud queda atendida
        return self.repositorio.actualizar(usuario, **datos)
