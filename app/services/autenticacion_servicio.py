import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Usuario
from app.repositories import RepositorioCategorias, RepositorioUsuarios
from app.schemas import RegistroUsuario
from app.seguridad import cifrar_contrasena, hash_ficticio, leer_token, verificar_contrasena
from app.services.excepciones import (
    ConflictoDeDatos,
    ErrorDeValidacion,
    NoAutenticado,
    SinPermiso,
)

CATEGORIAS_INICIALES = [
    "Salario", "Comida", "Transporte", "Vivienda",
    "Servicios", "Salud", "Entretenimiento",
]
PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MENSAJE_SESION_INVALIDA = "Tu sesión no es válida o expiró. Inicia sesión de nuevo."


def validar_contrasena(contrasena: str) -> None:
    """Regla: mínimo 8 caracteres, con al menos una letra y un número."""
    if (
        len(contrasena) < 8
        or not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]", contrasena)
        or not re.search(r"\d", contrasena)
    ):
        raise ErrorDeValidacion(
            "La contraseña debe tener al menos 8 caracteres e incluir letras y números"
        )


class ServicioAutenticacion:
    """Registro de cuentas, inicio de sesión y validación de sesiones."""

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = RepositorioUsuarios(db)

    def registrar(self, datos: RegistroUsuario) -> Usuario:
        nombre = datos.nombre.strip()
        email = datos.email.strip().lower()
        if not nombre:
            raise ErrorDeValidacion("El nombre es obligatorio")
        if not PATRON_EMAIL.match(email):
            raise ErrorDeValidacion("El correo electrónico no es válido")
        validar_contrasena(datos.contrasena)
        if self.repositorio.obtener_por_email(email) is not None:
            raise ConflictoDeDatos("Ya existe una cuenta registrada con ese correo")

        usuario = self.repositorio.crear(
            nombre=nombre, email=email, contrasena_hash=cifrar_contrasena(datos.contrasena)
        )
        if datos.crear_categorias_iniciales:
            RepositorioCategorias(self.db, usuario.id).crear_varias(CATEGORIAS_INICIALES)
        return usuario

    def autenticar(self, email: str, contrasena: str) -> Usuario:
        usuario = self.repositorio.obtener_por_email(email.strip().lower())
        # Siempre se verifica un hash, exista o no el correo (mismo tiempo de respuesta).
        hash_guardado = usuario.contrasena_hash if usuario else hash_ficticio()
        contrasena_correcta = verificar_contrasena(contrasena, hash_guardado)
        if usuario is None or not contrasena_correcta:
            raise NoAutenticado("Correo o contraseña incorrectos")
        if not usuario.activo:
            raise SinPermiso("Tu cuenta está desactivada. Contacta al administrador.")
        return usuario

    def usuario_desde_token(self, token: Optional[str]) -> Usuario:
        """Se ejecuta en cada petición protegida: valida el token y la cuenta."""
        usuario_id = leer_token(token) if token else None
        if usuario_id is None:
            raise NoAutenticado(MENSAJE_SESION_INVALIDA)
        usuario = self.repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise NoAutenticado(MENSAJE_SESION_INVALIDA)
        if not usuario.activo:
            # 401 (no 403) para que la interfaz cierre la sesión de inmediato.
            raise NoAutenticado("Tu cuenta fue desactivada. Contacta al administrador.")
        return usuario
