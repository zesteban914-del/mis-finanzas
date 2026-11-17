from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Movimiento, RolUsuario, Usuario


class RepositorioUsuarios:
    """Operaciones sobre las cuentas de usuario."""

    def __init__(self, db: Session):
        self.db = db

    def crear(
        self,
        nombre: str,
        email: str,
        contrasena_hash: str,
        rol: RolUsuario = RolUsuario.USUARIO,
    ) -> Usuario:
        usuario = Usuario(
            nombre=nombre, email=email, contrasena_hash=contrasena_hash, rol=rol
        )
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.db.get(Usuario, usuario_id)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def listar_con_cantidad_de_movimientos(self) -> List[Tuple[Usuario, int]]:
        """Cada usuario con cuántos movimientos tiene (sin montos)."""
        return (
            self.db.query(Usuario, func.count(Movimiento.id))
            .outerjoin(Movimiento, Movimiento.usuario_id == Usuario.id)
            .group_by(Usuario.id)
            .order_by(Usuario.creado_en, Usuario.id)
            .all()
        )

    def actualizar(self, usuario: Usuario, **cambios) -> Usuario:
        for campo, valor in cambios.items():
            setattr(usuario, campo, valor)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def contar(self, **filtros) -> int:
        return self.db.query(func.count(Usuario.id)).filter_by(**filtros).scalar() or 0

    def contar_movimientos(self) -> int:
        return self.db.query(func.count(Movimiento.id)).scalar() or 0
