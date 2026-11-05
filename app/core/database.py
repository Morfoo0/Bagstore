from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def crear_engine(database_url: str) -> Engine:
    opciones: dict = {
        "echo": settings.database_echo,
        "pool_pre_ping": True,
    }
    if database_url.startswith("sqlite") and ":memory:" in database_url:
        opciones["connect_args"] = {"check_same_thread": False}
        opciones["poolclass"] = StaticPool
    return create_engine(database_url, **opciones)


engine = crear_engine(settings.database_url)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verificar_conexion() -> None:
    with engine.connect() as conexion:
        conexion.execute(text("SELECT 1"))
