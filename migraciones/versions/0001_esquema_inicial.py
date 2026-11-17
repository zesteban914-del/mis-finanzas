"""Esquema inicial: usuarios, categorías, movimientos y presupuestos.

Revisión: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        sa.Column("email", sa.String(120), nullable=False),
        sa.Column("contrasena_hash", sa.String(255), nullable=False),
        sa.Column("rol", sa.Enum("USUARIO", "ADMIN", name="rol_usuario"), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usuarios_id", "usuarios", ["id"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.UniqueConstraint("usuario_id", "nombre", name="uq_categoria_usuario_nombre"),
    )
    op.create_index("ix_categorias_id", "categorias", ["id"])
    op.create_index("ix_categorias_usuario_id", "categorias", ["usuario_id"])

    op.create_table(
        "movimientos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.Enum("INGRESO", "GASTO", name="tipo_movimiento"), nullable=False),
        sa.Column("monto", sa.Numeric(14, 2), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_index("ix_movimientos_id", "movimientos", ["id"])
    op.create_index("ix_movimientos_fecha", "movimientos", ["fecha"])
    op.create_index("ix_movimientos_usuario_id", "movimientos", ["usuario_id"])

    op.create_table(
        "presupuestos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mes", sa.String(7), nullable=False),
        sa.Column("limite", sa.Numeric(14, 2), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.UniqueConstraint("usuario_id", "mes", name="uq_presupuesto_usuario_mes"),
    )
    op.create_index("ix_presupuestos_id", "presupuestos", ["id"])
    op.create_index("ix_presupuestos_mes", "presupuestos", ["mes"])
    op.create_index("ix_presupuestos_usuario_id", "presupuestos", ["usuario_id"])


def downgrade() -> None:
    for tabla in ("presupuestos", "movimientos", "categorias", "usuarios"):
        op.drop_table(tabla)
    for tipo in ("tipo_movimiento", "rol_usuario"):
        sa.Enum(name=tipo).drop(op.get_bind(), checkfirst=True)
