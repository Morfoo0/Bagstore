from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.main import app
from app.models.sesion import Sesion
from app.models.usuario import Usuario
from app.schemas.common import Estado

ADMIN_EMAIL = "admin@bagstore.com"
ADMIN_PASSWORD = "admin-test-123"


def test_registro_crea_cliente(client: TestClient) -> None:
    response = client.post(
        "/api/auth/registro",
        json={
            "nombre": "Nueva Cliente",
            "email": "nueva@bagstore.com",
            "password": "password-seguro-123",
            "telefono": "+5215512345678",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nueva@bagstore.com"
    assert body["rol"] == "cliente"
    assert body["estado"] == "activo"
    assert "password" not in body
    assert "password_hash" not in body


def test_registro_almacena_password_hasheada(
    public_client: TestClient,
    db_session: Session,
) -> None:
    password = "password-seguro-123"
    response = public_client.post(
        "/api/auth/registro",
        json={
            "nombre": "Hash Seguro",
            "email": "hash@bagstore.com",
            "password": password,
        },
    )
    assert response.status_code == 201

    usuario = db_session.scalars(
        select(Usuario).where(Usuario.email == "hash@bagstore.com")
    ).first()
    assert usuario is not None
    assert usuario.password_hash != password
    assert usuario.password_hash.startswith("$argon2")


def test_registro_rechaza_email_duplicado(client: TestClient) -> None:
    datos = {
        "nombre": "Duplicada",
        "email": "duplicada@bagstore.com",
        "password": "password-seguro-123",
    }
    assert client.post("/api/auth/registro", json=datos).status_code == 201
    response = client.post("/api/auth/registro", json=datos)

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "CONFLICTO_UNICIDAD"
    assert response.json()["error"]["detalles"][0]["campo"] == "email"


def test_registro_no_permite_asignarse_rol_admin(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/auth/registro",
        json={
            "nombre": "Intrusa",
            "email": "intrusa@bagstore.com",
            "password": "password-seguro-123",
            "rol": "administrador",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["codigo"] == "VALIDACION_FALLIDA"
    assert body["error"]["detalles"][0]["campo"] == "rol"


def test_login_admin_y_sesion_activa(admin_client: TestClient) -> None:
    sesion = admin_client.get("/api/auth/sesion")

    assert sesion.status_code == 200
    body = sesion.json()
    assert body["autenticado"] is True
    assert body["usuario"]["email"] == ADMIN_EMAIL
    assert body["usuario"]["rol"] == "administrador"


def test_login_con_password_incorrecta(
    public_client: TestClient,
) -> None:
    response = public_client.post(
        "/api/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": "password-incorrecta",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_login_con_email_inexistente(public_client: TestClient) -> None:
    response = public_client.post(
        "/api/auth/login",
        json={
            "email": "no-existe@bagstore.com",
            "password": "password-seguro-123",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_sesion_requiere_token(public_client: TestClient) -> None:
    response = public_client.get("/api/auth/sesion")

    assert response.status_code == 401
    assert response.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_sesion_rechaza_token_invalido(public_client: TestClient) -> None:
    response = public_client.get(
        "/api/auth/sesion",
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_logout_revoca_sesion(admin_client: TestClient) -> None:
    response = admin_client.post("/api/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    assert admin_client.get("/api/auth/sesion").status_code == 401
    assert admin_client.post("/api/auth/logout").status_code == 204


def test_cliente_no_puede_crear_productos(
    cliente_client: TestClient,
) -> None:
    response = cliente_client.post(
        "/api/productos",
        json={
            "nombre": "Producto Cliente",
            "precio": "100.00",
            "sku": "BAG-CLI-001",
            "categoria_id": 2,
            "existencias": 1,
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["codigo"] == "ACCESO_DENEGADO"


def test_publico_no_puede_crear_productos(
    public_client: TestClient,
) -> None:
    response = public_client.post(
        "/api/productos",
        json={
            "nombre": "Producto Público",
            "precio": "100.00",
            "sku": "BAG-PUB-001",
            "categoria_id": 2,
            "existencias": 1,
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_admin_puede_crear_productos(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/api/productos",
        json={
            "nombre": "Producto Admin",
            "precio": "100.00",
            "sku": "BAG-ADM-001",
            "categoria_id": 2,
            "existencias": 1,
        },
    )

    assert response.status_code == 201
    assert response.json()["sku"] == "BAG-ADM-001"


def test_sesion_expirada_es_rechazada(
    public_client: TestClient,
    db_session: Session,
) -> None:
    login = public_client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    token = login.json()["access_token"]
    sesion = db_session.scalars(
        select(Sesion).where(Sesion.token_hash == hash_token(token))
    ).first()
    assert sesion is not None
    sesion.expira_en = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    response = public_client.get(
        "/api/auth/sesion",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_usuario_inactivo_no_puede_usar_sesion(
    public_client: TestClient,
    db_session: Session,
) -> None:
    login = public_client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    token = login.json()["access_token"]
    usuario = db_session.scalars(
        select(Usuario).where(Usuario.email == ADMIN_EMAIL)
    ).first()
    assert usuario is not None
    usuario.estado = Estado.INACTIVO
    db_session.commit()

    response = public_client.get(
        "/api/auth/sesion",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["codigo"] == "ACCESO_DENEGADO"


def test_admin_puede_ver_productos_inactivos(
    admin_client: TestClient,
) -> None:
    detalle = admin_client.get("/api/productos/4")
    listado = admin_client.get(
        "/api/productos",
        params={"estado": "inactivo"},
    )

    assert detalle.status_code == 200
    assert detalle.json()["estado"] == "inactivo"
    assert listado.status_code == 200
    assert listado.json()["paginacion"]["total"] == 2


def test_cliente_no_puede_ver_productos_inactivos(
    cliente_client: TestClient,
) -> None:
    detalle = cliente_client.get("/api/productos/4")
    listado = cliente_client.get(
        "/api/productos",
        params={"estado": "inactivo"},
    )

    assert detalle.status_code == 404
    assert listado.status_code == 403


def test_admin_puede_ver_coleccion_inactiva(
    admin_client: TestClient,
) -> None:
    detalle = admin_client.get("/api/colecciones/2")
    listado = admin_client.get(
        "/api/colecciones",
        params={"estado": "inactivo"},
    )

    assert detalle.status_code == 200
    assert detalle.json()["estado"] == "inactivo"
    assert listado.status_code == 200
    assert listado.json()["paginacion"]["total"] == 1


def test_admin_puede_ver_categoria_inactiva(
    admin_client: TestClient,
) -> None:
    creada = admin_client.post(
        "/api/categorias",
        json={"nombre": "Solo Admin", "estado": "inactivo"},
    )
    categoria_id = creada.json()["id"]

    detalle = admin_client.get(f"/api/categorias/{categoria_id}")
    listado = admin_client.get(
        "/api/categorias",
        params={"estado": "inactivo"},
    )

    assert detalle.status_code == 200
    assert detalle.json()["estado"] == "inactivo"
    assert listado.status_code == 200
    assert listado.json()["paginacion"]["total"] == 1


def test_token_de_sesion_se_almacena_hasheado(
    public_client: TestClient,
    db_session: Session,
) -> None:
    login = public_client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    token = login.json()["access_token"]

    sesion = db_session.scalars(
        select(Sesion).where(Sesion.token_hash == hash_token(token))
    ).first()

    assert sesion is not None
    assert sesion.token_hash != token


def test_cliente_login_y_sesion(cliente_client: TestClient) -> None:
    response = cliente_client.get("/api/auth/sesion")

    assert response.status_code == 200
    body = response.json()
    assert body["usuario"]["email"] == "cliente@bagstore.com"
    assert body["usuario"]["rol"] == "cliente"


def test_persistencia_entre_instancias_de_app(
    admin_client: TestClient,
) -> None:
    creado = admin_client.post(
        "/api/productos",
        json={
            "nombre": "Producto Persistente",
            "precio": "100.00",
            "sku": "BAG-PER-001",
            "categoria_id": 2,
            "existencias": 1,
        },
    )
    producto_id = creado.json()["id"]

    with TestClient(app) as nueva_app:
        login = nueva_app.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        token = login.json()["access_token"]
        response = nueva_app.get(
            f"/api/productos/{producto_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["sku"] == "BAG-PER-001"
