from datetime import date, datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models import Plan, RolUsuario, TipoCuenta, Usuario
from app.repositories import RepositorioUsuarios
from app.repositories.movimiento_repositorio import rango_del_mes
from app.schemas.usuario import ActividadMes
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
            actividad_por_mes=self._actividad_por_mes(),
        )

    def _actividad_por_mes(self, meses: int = 6) -> List[ActividadMes]:
        """Cuentas nuevas y movimientos de los últimos meses (solo cantidades)."""
        hoy = date.today()
        actividad = []
        for atras in range(meses - 1, -1, -1):
            total = hoy.year * 12 + hoy.month - 1 - atras
            anio, mes = total // 12, total % 12 + 1
            inicio, fin = rango_del_mes(anio, mes)
            desde = datetime(inicio.year, inicio.month, 1, tzinfo=timezone.utc)
            hasta = datetime(fin.year, fin.month, 1, tzinfo=timezone.utc)
            actividad.append(
                ActividadMes(
                    mes=f"{anio:04d}-{mes:02d}",
                    cuentas_personales=self.repositorio.contar_registros_entre(desde, hasta, TipoCuenta.PERSONAL),
                    cuentas_negocio=self.repositorio.contar_registros_entre(desde, hasta, TipoCuenta.NEGOCIO),
                    movimientos=self.repositorio.contar_movimientos_entre(inicio, fin),
                )
            )
        return actividad

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
            if datos["plan"] == Plan.PRO:
                datos["solicito_pro_en"] = None  # la solicitud queda atendida
        if datos.pop("descartar_solicitud", False):
            datos["solicito_pro_en"] = None
        return self.repositorio.actualizar(usuario, **datos)
