"""Configuración de la base de datos y de las sesiones de SQLAlchemy."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

URL_BASE_DE_DATOS = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/control_gastos",
)


def crear_motor(url: str):
    """Crea el motor de base de datos.

    SQLite en memoria (usado en las pruebas) necesita StaticPool y
    check_same_thread=False para compartir una única conexión entre
    todas las peticiones; de lo contrario cada conexión vería una
    base de datos vacía distinta.
    """
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url)


engine = crear_motor(URL_BASE_DE_DATOS)
SesionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def obtener_db():
    """Entrega una sesión por petición (se usa con Depends en los controladores)."""
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
