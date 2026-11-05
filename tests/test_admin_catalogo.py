from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.producto import Producto


def test_admin_lista_colecciones_incluye_inactivas(
    admin_client: TestClient,
    public_client: TestClient,
    cliente_client: TestClient,
) -> None:
    admin = admin_client.get("/api/admin/colecciones")
    publico = public_client.get("/api/colecciones")
    cliente = cliente_client.get("/api/admin/colecciones")
    sin_auth = public_client.get("/api/admin/colecciones")

    assert admin.status_code == 200
    assert [item["slug"] for item in admin.json()["datos"]] == [
        "la-coleccion",
        "archivo",
    ]
    assert publico.json()["paginacion"]["total"] == 1
    assert cliente.status_code == 403
    assert sin_auth.status_code == 401


def test_admin_productos_de_coleccion_incluye_inactivos(
    admin_client: TestClient,
    public_client: TestClient,
) -> None:
    actualizada = admin_client.put(
        "/api/colecciones/2",
        json={
            "nombre": "Archivo",
            "estado": "inactivo",
            "producto_ids": [2, 4],
        },
    )
    assert actualizada.status_code == 200

    todos = admin_client.get(
        "/api/admin/colecciones/2/productos",
        params={"estado": "todos"},
    )
    inactivos = admin_client.get(
        "/api/admin/colecciones/2/productos",
        params={"estado": "inactivo"},
    )
    publico = public_client.get(
        "/api/productos",
        params={"coleccion": "archivo"},
    )

    assert todos.status_code == 200
    assert {item["id"] for item in todos.json()["datos"]} == {2, 4}
    assert [item["id"] for item in inactivos.json()["datos"]] == [4]
    assert publico.json()["paginacion"]["total"] == 0


def test_admin_puede_desactivar_y_reactivar_producto(
    admin_client: TestClient,
    public_client: TestClient,
    cliente_client: TestClient,
) -> None:
    desactivado = admin_client.put(
        "/api/admin/productos/1/estado",
        json={"estado": "inactivo"},
    )

    assert desactivado.status_code == 200
    assert desactivado.json()["estado"] == "inactivo"
    assert public_client.get("/api/productos/1").status_code == 404
    assert admin_client.get("/api/productos/1").status_code == 200
    assert cliente_client.put(
        "/api/admin/productos/1/estado",
        json={"estado": "activo"},
    ).status_code == 403
    assert public_client.put(
        "/api/admin/productos/1/estado",
        json={"estado": "activo"},
    ).status_code == 401

    reactivado = admin_client.put(
        "/api/admin/productos/1/estado",
        json={"estado": "activo"},
    )

    assert reactivado.status_code == 200
    assert reactivado.json()["estado"] == "activo"
    assert public_client.get("/api/productos/1").status_code == 200


def test_no_reactivar_producto_con_categoria_inactiva(
    admin_client: TestClient,
) -> None:
    categoria = admin_client.post(
        "/api/categorias",
        json={"nombre": "Temporal"},
    ).json()
    producto = admin_client.post(
        "/api/productos",
        json={
            "nombre": "Producto Temporal",
            "precio": "100.00",
            "sku": "BAG-TMP-001",
            "categoria_id": categoria["id"],
            "existencias": 1,
        },
    ).json()
    admin_client.put(
        f"/api/admin/productos/{producto['id']}/estado",
        json={"estado": "inactivo"},
    )
    assert admin_client.put(
        f"/api/categorias/{categoria['id']}",
        json={"nombre": "Temporal", "estado": "inactivo"},
    ).status_code == 200

    response = admin_client.put(
        f"/api/admin/productos/{producto['id']}/estado",
        json={"estado": "activo"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "categoria_id"


def test_eliminar_producto_es_logico(
    admin_client: TestClient,
    db_session: Session,
) -> None:
    response = admin_client.delete("/api/productos/1")

    assert response.status_code == 204
    assert admin_client.get("/api/productos/1").status_code == 404
    assert admin_client.get(
        "/api/productos",
        params={"estado": "todos"},
    ).json()["paginacion"]["total"] == 9

    db_session.expire_all()
    producto = db_session.scalars(
        select(Producto).where(Producto.id == 1)
    ).first()
    assert producto is not None
    assert producto.eliminado_en is not None


def test_openapi_incluye_endpoints_fase2(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/colores" in paths
    assert "/api/productos/{producto_id}/colores" in paths
    assert "/api/productos/{producto_id}/imagenes" in paths
    assert "/api/admin/colecciones" in paths
    assert "/api/admin/colecciones/{coleccion_id}/productos" in paths
    assert "/api/admin/productos/{producto_id}/estado" in paths


def test_admin_consulta_productos_inactivos(
    admin_client: TestClient,
    public_client: TestClient,
) -> None:
    todos = admin_client.get(
        "/api/productos",
        params={"estado": "todos"},
    )
    inactivos = admin_client.get(
        "/api/productos",
        params={"estado": "inactivo"},
    )
    publico = public_client.get(
        "/api/productos",
        params={"estado": "todos"},
    )

    assert todos.json()["paginacion"]["total"] == 10
    assert inactivos.json()["paginacion"]["total"] == 2
    assert publico.status_code == 403
