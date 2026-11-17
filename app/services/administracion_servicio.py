from typing import List

from sqlalchemy.orm import Session

from app.models import RolUsuario, Usuario
from app.repositories import RepositorioUsuarios
from app.schemas import (
    CambioUsuarioAdmin,
    EstadisticasAdmin,
    UsuarioAdminRespuesta,
    UsuarioRespuesta,
)
from app.services.excepciones import ErrorDeValidacion, RecursoNoEncontrado


class ServicioAdministracion:
    """Gestión de cuentas por parte de un administrador.

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
        return EstadisticasAdmin(
            total_usuarios=self.repositorio.contar(),
            usuarios_activos=self.repositorio.contar(activo=True),
            administradores=self.repositorio.contar(rol=RolUsuario.ADMIN),
            movimientos_registrados=self.repositorio.contar_movimientos(),
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
        return self.repositorio.actualizar(usuario, **datos)
