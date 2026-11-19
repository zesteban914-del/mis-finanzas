"""Configuración de la base de datos y de las sesiones de SQLAlchemy."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

URL_LOCAL = "postgresql+psycopg2://postgres:postgres@localhost:5434/control_gastos"


def normalizar_url(url: str) -> str:
    """Acepta las URLs que entregan los proveedores en la nube.

    Neon/Vercel y otros usan el prefijo `postgres://`, que SQLAlchemy ya no
    reconoce; se cambia por `postgresql+psycopg2://` (el controlador instalado).
    """
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg2://" + url[len(prefijo):]
    return url


# DATABASE_URL: local o la que crea la integración de Neon en Vercel.
URL_BASE_DE_DATOS = normalizar_url(
    os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or URL_LOCAL
)


def crear_motor(url: str):
    """Crea el motor de base de datos.

    - SQLite en memoria (pruebas) necesita StaticPool y check_same_thread=False
      para compartir una única conexión; si no, cada conexión vería una base vacía.
    - En Vercel (funciones que se encienden y apagan) no se guardan conexiones
      abiertas entre peticiones (NullPool); el pooler de Neon las administra.
    """
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if os.getenv("VERCEL"):
        return create_engine(url, poolclass=NullPool)
    return create_engine(url, pool_pre_ping=True)


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
