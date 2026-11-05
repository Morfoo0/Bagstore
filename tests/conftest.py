import os

os.environ["DATABASE_URL"] = (
    os.getenv("TEST_DATABASE_URL")
    or "sqlite+pysqlite:///:memory:"
)
os.environ["DATABASE_ECHO"] = "false"
os.environ["SESSION_TTL_MINUTES"] = "60"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.scripts.seed import crear_admin, seed_catalogo

ADMIN_EMAIL = "admin@bagstore.com"
ADMIN_PASSWORD = "admin-test-123"
CLIENTE_PASSWORD = "cliente-test-123"


@pytest.fixture
def db_limpia() -> None:
    Base.metadata.drop_all(engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conexion:
            for tipo in (
                "estado_producto",
                "estado_coleccion",
                "estado_categoria",
                "estado_usuario",
                "rol_usuario",
            ):
                conexion.execute(
                    text(f"DROP TYPE IF EXISTS {tipo} CASCADE")
                )
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_catalogo(session)
        crear_admin(session, ADMIN_EMAIL, ADMIN_PASSWORD)
        session.commit()
    yield


@pytest.fixture
def db_session(db_limpia: None) -> Session:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def public_client(db_limpia: None) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_client(db_limpia: None) -> TestClient:
    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        test_client.headers.update(
            {"Authorization": f"Bearer {token}"}
        )
        yield test_client


@pytest.fixture
def cliente_client(db_limpia: None) -> TestClient:
    with TestClient(app) as test_client:
        registro = test_client.post(
            "/api/auth/registro",
            json={
                "nombre": "Cliente de Prueba",
                "email": "cliente@bagstore.com",
                "password": CLIENTE_PASSWORD,
                "telefono": "+5215512345678",
            },
        )
        assert registro.status_code == 201
        login = test_client.post(
            "/api/auth/login",
            json={
                "email": "cliente@bagstore.com",
                "password": CLIENTE_PASSWORD,
            },
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        test_client.headers.update(
            {"Authorization": f"Bearer {token}"}
        )
        yield test_client


class ClienteAdminEscritura(TestClient):
    def __init__(self, app, token: str) -> None:
        super().__init__(app)
        self._token = token

    def request(self, method, url, **kwargs):
        if (
            method.upper() in {"POST", "PUT", "DELETE", "PATCH"}
            and not str(url).startswith("/api/auth/")
        ):
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault(
                "Authorization", f"Bearer {self._token}"
            )
            kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


@pytest.fixture
def client(admin_client: TestClient) -> TestClient:
    autorizacion = admin_client.headers["Authorization"]
    token = autorizacion.split(" ", 1)[1]
    with ClienteAdminEscritura(app, token) as test_client:
        yield test_client
