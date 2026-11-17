"""Tipos de cuenta, planes, equipo y funciones de negocio.

Agrega a usuarios: tipo de cuenta, plan, datos personales/de negocio y
equipo. Crea cajas, transferencias, recurrentes, presupuestos por
categoría, metas, deudas y comprobantes. Los datos existentes se
conservan: las cuentas actuales quedan como PERSONAL en plan GRATIS.

Revisión: 0002
Anterior: 0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TIPOS_NUEVOS = {
    "tipo_cuenta": ("PERSONAL", "NEGOCIO"),
    "plan_suscripcion": ("GRATIS", "PRO"),
    "rol_negocio": ("PROPIETARIO", "EMPLEADO", "CONTADOR"),
    "tipo_caja": ("EFECTIVO", "BANCO", "BILLETERA"),
    "tipo_deuda": ("POR_PAGAR", "POR_COBRAR"),
}


def enum(nombre: str):
    """Referencia a un tipo ENUM ya creado (no lo vuelve a crear)."""
    if op.get_bind().dialect.name == "postgresql":
        return postgresql.ENUM(name=nombre, create_type=False)
    return sa.Enum(*TIPOS_NUEVOS.get(nombre, ("INGRESO", "GASTO")), name=nombre)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for nombre, valores in TIPOS_NUEVOS.items():
            postgresql.ENUM(*valores, name=nombre).create(bind, checkfirst=True)

    # Usuarios: tipo de cuenta, plan, perfil y equipo
    op.add_column("usuarios", sa.Column("tipo_cuenta", enum("tipo_cuenta"), nullable=False, server_default="PERSONAL"))
    op.add_column("usuarios", sa.Column("plan", enum("plan_suscripcion"), nullable=False, server_default="GRATIS"))
    op.add_column("usuarios", sa.Column("solicito_pro_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuarios", sa.Column("acepto_terminos_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuarios", sa.Column("objetivo", sa.String(40), nullable=True))
    op.add_column("usuarios", sa.Column("sector", sa.String(60), nullable=True))
    op.add_column("usuarios", sa.Column("nit", sa.String(20), nullable=True))
    op.add_column("usuarios", sa.Column("responsable", sa.String(80), nullable=True))
    op.add_column("usuarios", sa.Column("negocio_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True))
    op.add_column("usuarios", sa.Column("rol_negocio", enum("rol_negocio"), nullable=True))
    op.create_index("ix_usuarios_negocio_id", "usuarios", ["negocio_id"])

    op.create_table(
        "cajas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(60), nullable=False),
        sa.Column("tipo", enum("tipo_caja"), nullable=False),
        sa.Column("saldo_inicial", sa.Numeric(14, 2), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.UniqueConstraint("usuario_id", "nombre", name="uq_caja_usuario_nombre"),
    )
    op.create_index("ix_cajas_id", "cajas", ["id"])
    op.create_index("ix_cajas_usuario_id", "cajas", ["usuario_id"])

    op.create_table(
        "transferencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("origen_id", sa.Integer(), sa.ForeignKey("cajas.id"), nullable=False),
        sa.Column("destino_id", sa.Integer(), sa.ForeignKey("cajas.id"), nullable=False),
        sa.Column("monto", sa.Numeric(14, 2), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_index("ix_transferencias_id", "transferencias", ["id"])
    op.create_index("ix_transferencias_usuario_id", "transferencias", ["usuario_id"])

    op.create_table(
        "recurrentes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", enum("tipo_movimiento"), nullable=False),
        sa.Column("monto", sa.Numeric(14, 2), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("dia_del_mes", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), nullable=False),
        sa.Column("caja_id", sa.Integer(), sa.ForeignKey("cajas.id"), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("mes_inicio", sa.String(7), nullable=False),
        sa.Column("ultimo_mes_generado", sa.String(7), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_index("ix_recurrentes_id", "recurrentes", ["id"])
    op.create_index("ix_recurrentes_usuario_id", "recurrentes", ["usuario_id"])

    # Movimientos: caja, autor y recurrente de origen
    op.add_column("movimientos", sa.Column("caja_id", sa.Integer(), sa.ForeignKey("cajas.id"), nullable=True))
    op.add_column(
        "movimientos",
        sa.Column("registrado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "movimientos",
        sa.Column("recurrente_id", sa.Integer(), sa.ForeignKey("recurrentes.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_movimientos_caja_id", "movimientos", ["caja_id"])

    op.create_table(
        "presupuestos_categoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False),
        sa.Column("limite", sa.Numeric(14, 2), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.UniqueConstraint("usuario_id", "categoria_id", name="uq_presupuesto_categoria"),
    )
    op.create_index("ix_presupuestos_categoria_id", "presupuestos_categoria", ["id"])
    op.create_index("ix_presupuestos_categoria_usuario_id", "presupuestos_categoria", ["usuario_id"])

    op.create_table(
        "metas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        sa.Column("monto_objetivo", sa.Numeric(14, 2), nullable=False),
        sa.Column("monto_ahorrado", sa.Numeric(14, 2), nullable=False),
        sa.Column("fecha_limite", sa.Date(), nullable=True),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_index("ix_metas_id", "metas", ["id"])
    op.create_index("ix_metas_usuario_id", "metas", ["usuario_id"])

    op.create_table(
        "deudas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", enum("tipo_deuda"), nullable=False),
        sa.Column("contraparte", sa.String(80), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("monto_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("monto_pagado", sa.Numeric(14, 2), nullable=False),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_index("ix_deudas_id", "deudas", ["id"])
    op.create_index("ix_deudas_usuario_id", "deudas", ["usuario_id"])

    op.create_table(
        "comprobantes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "movimiento_id", sa.Integer(), sa.ForeignKey("movimientos.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),
        sa.Column("nombre_archivo", sa.String(150), nullable=False),
        sa.Column("tipo_contenido", sa.String(60), nullable=False),
        sa.Column("tamano", sa.Integer(), nullable=False),
        sa.Column("contenido", sa.LargeBinary(), nullable=False),
        sa.Column("subido_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comprobantes_id", "comprobantes", ["id"])


def downgrade() -> None:
    for tabla in ("comprobantes", "deudas", "metas", "presupuestos_categoria"):
        op.drop_table(tabla)
    op.drop_index("ix_movimientos_caja_id", "movimientos")
    for columna in ("recurrente_id", "registrado_por_id", "caja_id"):
        op.drop_column("movimientos", columna)
    for tabla in ("recurrentes", "transferencias", "cajas"):
        op.drop_table(tabla)
    op.drop_index("ix_usuarios_negocio_id", "usuarios")
    for columna in (
        "rol_negocio", "negocio_id", "responsable", "nit", "sector", "objetivo",
        "acepto_terminos_en", "solicito_pro_en", "plan", "tipo_cuenta",
    ):
        op.drop_column("usuarios", columna)
    for nombre in TIPOS_NUEVOS:
        postgresql.ENUM(name=nombre).drop(op.get_bind(), checkfirst=True)
