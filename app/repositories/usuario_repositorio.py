from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import func

from app.models import Movimiento, Plan, RolUsuario, TipoCuenta, Usuario
from app.planes import PRECIOS


class RepositorioUsuarios:
    """Operaciones sobre las cuentas de usuario."""

    def __init__(self, db):
        self.db = db

    def crear(self, **datos) -> Usuario:
        usuario = Usuario(**datos)
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.db.get(Usuario, usuario_id)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def listar_con_cantidad_de_movimientos(self) -> List[Tuple[Usuario, int]]:
        """Cada usuario con cuántos movimientos tiene su cuenta (sin montos)."""
        return (
            self.db.query(Usuario, func.count(Movimiento.id))
            .outerjoin(Movimiento, Movimiento.usuario_id == Usuario.id)
            .group_by(Usuario.id)
            .order_by(Usuario.creado_en, Usuario.id)
            .all()
        )

    def listar_miembros(self, negocio_id: int) -> List[Usuario]:
        return (
            self.db.query(Usuario)
            .filter(Usuario.negocio_id == negocio_id)
            .order_by(Usuario.creado_en, Usuario.id)
            .all()
        )

    def actualizar(self, usuario: Usuario, **cambios) -> Usuario:
        for campo, valor in cambios.items():
            setattr(usuario, campo, valor)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def eliminar(self, usuario: Usuario) -> None:
        self.db.delete(usuario)
        self.db.commit()

    def contar(self, *condiciones, **filtros) -> int:
        return (
            self.db.query(func.count(Usuario.id))
            .filter(*condiciones)
            .filter_by(**filtros)
            .scalar()
            or 0
        )

    def contar_titulares(self, **filtros) -> int:
        """Cuentas de clientes: sin miembros de un equipo ni administradores."""
        return self.contar(Usuario.negocio_id.is_(None), Usuario.rol == RolUsuario.USUARIO, **filtros)

    def contar_movimientos(self) -> int:
        return self.db.query(func.count(Movimiento.id)).scalar() or 0

    def contar_registros_entre(self, inicio: datetime, fin: datetime, tipo: TipoCuenta) -> int:
        """Cuentas de clientes creadas en [inicio, fin)."""
        return self.contar(
            Usuario.negocio_id.is_(None),
            Usuario.rol == RolUsuario.USUARIO,
            Usuario.creado_en >= inicio,
            Usuario.creado_en < fin,
            tipo_cuenta=tipo,
        )

    def contar_movimientos_entre(self, inicio: date, fin: date) -> int:
        return (
            self.db.query(func.count(Movimiento.id))
            .filter(Movimiento.fecha >= inicio, Movimiento.fecha < fin)
            .scalar()
            or 0
        )

    def ingreso_mensual_estimado(self) -> int:
        """Suma del precio de las cuentas Pro activas (ingreso recurrente mensual)."""
        total = 0
        for tipo in TipoCuenta:
            cantidad = self.contar_titulares(tipo_cuenta=tipo, plan=Plan.PRO, activo=True)
            total += cantidad * PRECIOS[(tipo, Plan.PRO)]
        return total
