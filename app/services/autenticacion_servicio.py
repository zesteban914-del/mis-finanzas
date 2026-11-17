from typing import Optional

from sqlalchemy.orm import Session

from app.catalogos import CATEGORIAS_INICIALES, OBJETIVOS_PERSONALES, SECTORES_NEGOCIO
from app.models import RolNegocio, TipoCuenta, Usuario
from app.models.usuario import ahora
from app.repositories import RepositorioCategorias, RepositorioUsuarios
from app.schemas import CambioContrasena, PerfilActualizar, RegistroUsuario
from app.seguridad import cifrar_contrasena, hash_ficticio, leer_token, verificar_contrasena
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    NoAutenticado,
    SinPermiso,
)
from app.services.validaciones import (
    texto_obligatorio,
    validar_contrasena,
    validar_email,
    validar_nit,
    validar_opcion,
)

MENSAJE_SESION_INVALIDA = "Tu sesión no es válida o expiró. Inicia sesión de nuevo."


class ServicioAutenticacion:
    """Registro de cuentas, inicio de sesión, perfil y validación de sesiones."""

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = RepositorioUsuarios(db)

    def registrar(self, datos: RegistroUsuario) -> Usuario:
        nombre = texto_obligatorio(datos.nombre, "nombre")
        email = validar_email(datos.email)
        validar_contrasena(datos.contrasena)
        if not datos.acepta_terminos:
            raise ErrorDeValidacion(
                "Debes aceptar los términos y la política de tratamiento de datos"
            )
        self.validar_email_disponible(email)

        if datos.tipo_cuenta == TipoCuenta.PERSONAL:
            datos_del_tipo = {
                "objetivo": validar_opcion(datos.objetivo, OBJETIVOS_PERSONALES, "objetivo"),
            }
        else:
            datos_del_tipo = {
                "sector": validar_opcion(datos.sector, SECTORES_NEGOCIO, "sector"),
                "nit": validar_nit(datos.nit),
                "responsable": (datos.responsable or "").strip() or None,
                "rol_negocio": RolNegocio.PROPIETARIO,
            }

        usuario = self.repositorio.crear(
            nombre=nombre,
            email=email,
            contrasena_hash=cifrar_contrasena(datos.contrasena),
            tipo_cuenta=datos.tipo_cuenta,
            acepto_terminos_en=ahora(),
            **datos_del_tipo,
        )
        if datos.crear_categorias_iniciales:
            RepositorioCategorias(self.db, usuario.id).crear_varias(
                CATEGORIAS_INICIALES[datos.tipo_cuenta]
            )
        return usuario

    def validar_email_disponible(self, email: str) -> None:
        if self.repositorio.obtener_por_email(email) is not None:
            raise ConflictoDeDatos("Ya existe una cuenta registrada con ese correo")

    def autenticar(self, email: str, contrasena: str) -> Usuario:
        usuario = self.repositorio.obtener_por_email((email or "").strip().lower())
        # Siempre se verifica un hash, exista o no el correo (mismo tiempo de respuesta).
        hash_guardado = usuario.contrasena_hash if usuario else hash_ficticio()
        contrasena_correcta = verificar_contrasena(contrasena, hash_guardado)
        if usuario is None or not contrasena_correcta:
            raise NoAutenticado("Correo o contraseña incorrectos")
        if not usuario.activo:
            raise SinPermiso("Tu cuenta está desactivada. Contacta al administrador.")
        if usuario.negocio_id and not usuario.negocio.activo:
            raise SinPermiso("La cuenta del negocio está desactivada.")
        return usuario

    def usuario_desde_token(self, token: Optional[str]) -> Usuario:
        """Se ejecuta en cada petición protegida: valida el token y la cuenta."""
        usuario_id = leer_token(token) if token else None
        usuario = self.repositorio.obtener_por_id(usuario_id) if usuario_id else None
        if usuario is None:
            raise NoAutenticado(MENSAJE_SESION_INVALIDA)
        # 401 (no 403) para que la interfaz cierre la sesión de inmediato.
        if not usuario.activo:
            raise NoAutenticado("Tu cuenta fue desactivada. Contacta al administrador.")
        if usuario.negocio_id and not usuario.negocio.activo:
            raise NoAutenticado("La cuenta del negocio fue desactivada.")
        return usuario

    def actualizar_perfil(self, usuario: Usuario, datos: PerfilActualizar) -> Usuario:
        cambios = {}
        if datos.nombre is not None:
            cambios["nombre"] = texto_obligatorio(datos.nombre, "nombre")
        # Los miembros de un equipo solo cambian su nombre; los datos del negocio son del propietario.
        if not usuario.negocio_id:
            if usuario.tipo_cuenta == TipoCuenta.PERSONAL and datos.objetivo is not None:
                cambios["objetivo"] = validar_opcion(datos.objetivo, OBJETIVOS_PERSONALES, "objetivo")
            if usuario.tipo_cuenta == TipoCuenta.NEGOCIO:
                if datos.sector is not None:
                    cambios["sector"] = validar_opcion(datos.sector, SECTORES_NEGOCIO, "sector")
                if datos.nit is not None:
                    cambios["nit"] = validar_nit(datos.nit)
                if datos.responsable is not None:
                    cambios["responsable"] = datos.responsable.strip() or None
        return self.repositorio.actualizar(usuario, **cambios)

    def cambiar_contrasena(self, usuario: Usuario, datos: CambioContrasena) -> None:
        if not verificar_contrasena(datos.actual, usuario.contrasena_hash):
            raise ErrorDeValidacion("La contraseña actual no es correcta")
        validar_contrasena(datos.nueva)
        if datos.nueva == datos.actual:
            raise ErrorDeValidacion("La nueva contraseña debe ser distinta de la actual")
        self.repositorio.actualizar(usuario, contrasena_hash=cifrar_contrasena(datos.nueva))
