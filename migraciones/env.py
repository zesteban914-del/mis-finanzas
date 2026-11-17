"""Entorno de Alembic: usa la misma conexión y modelos que la aplicación."""

from alembic import context

from app import models  # noqa: F401  (registra las tablas en Base.metadata)
from app.database import Base, engine

config = context.config
target_metadata = Base.metadata


def ejecutar_migraciones() -> None:
    # Si la app ya abrió una conexión (al arrancar), se reutiliza.
    conexion = config.attributes.get("connection")
    if conexion is not None:
        context.configure(connection=conexion, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    with engine.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


ejecutar_migraciones()
