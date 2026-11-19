"""Tabla de configuración interna (guarda la clave que firma las sesiones).

Revisión: 0003
Anterior: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuracion",
        sa.Column("clave", sa.String(60), primary_key=True),
        sa.Column("valor", sa.String(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("configuracion")
