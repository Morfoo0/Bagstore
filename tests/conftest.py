import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_categoria_repositorio,
    get_coleccion_repositorio,
    get_producto_repositorio,
)
from app.main import app


@pytest.fixture(autouse=True)
def repositorios_limpios() -> None:
    get_producto_repositorio.cache_clear()
    get_categoria_repositorio.cache_clear()
    get_coleccion_repositorio.cache_clear()
    yield
    get_producto_repositorio.cache_clear()
    get_categoria_repositorio.cache_clear()
    get_coleccion_repositorio.cache_clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
