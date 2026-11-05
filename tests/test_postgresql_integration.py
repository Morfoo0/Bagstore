import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import crear_engine, engine
from app.core.text import normalizar_texto
from app.models.categoria import Categoria
from app.schemas.common import Estado


pytestmark = pytest.mark.skipif(
    engine.dialect.name != "postgresql",
    reason="TEST_DATABASE_URL de PostgreSQL no está configurada.",
)


def test_conexion_postgresql() -> None:
    with engine.connect() as conexion:
        assert conexion.execute(text("SELECT 1")).scalar() == 1


def test_persistencia_en_postgresql(db_session: Session) -> None:
    categoria = Categoria(
        nombre="Persistencia PostgreSQL",
        nombre_busqueda=normalizar_texto("Persistencia PostgreSQL"),
        slug="persistencia-postgresql",
        descripcion=None,
        estado=Estado.ACTIVO,
        orden=99,
    )
    db_session.add(categoria)
    db_session.commit()

    nuevo_engine = crear_engine(settings.database_url)
    try:
        with Session(nuevo_engine) as nueva_sesion:
            encontrada = nueva_sesion.scalars(
                select(Categoria).where(
                    Categoria.slug == "persistencia-postgresql"
                )
            ).first()
            assert encontrada is not None
            assert encontrada.nombre == "Persistencia PostgreSQL"
    finally:
        nuevo_engine.dispose()
