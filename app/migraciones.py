"""Aplica las migraciones de Alembic pendientes al arrancar la aplicación."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.database import Base, engine

RAIZ = Path(__file__).resolve().parent.parent
REVISION_INICIAL = "0001"


def preparar_base_de_datos() -> None:
    """Deja la base con el esquema más reciente.

    - SQLite (pruebas): crea las tablas directamente desde los modelos.
    - PostgreSQL: aplica las migraciones pendientes. Si la base ya tenía las
      tablas iniciales pero no el historial de Alembic (se creó antes de usar
      migraciones), la marca como revisión inicial y aplica solo lo que falta.
    """
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)
        return

    configuracion = Config(str(RAIZ / "alembic.ini"))
    configuracion.set_main_option("script_location", str(RAIZ / "migraciones"))
    with engine.begin() as conexion:
        configuracion.attributes["connection"] = conexion
        tablas = inspect(conexion).get_table_names()
        if "usuarios" in tablas and "alembic_version" not in tablas:
            command.stamp(configuracion, REVISION_INICIAL)
        command.upgrade(configuracion, "head")
