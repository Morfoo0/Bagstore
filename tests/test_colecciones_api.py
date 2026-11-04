from fastapi.testclient import TestClient


def test_listar_colecciones_publicas(client: TestClient) -> None:
    response = client.get("/api/colecciones")

    assert response.status_code == 200
    body = response.json()
    assert [coleccion["slug"] for coleccion in body["datos"]] == [
        "la-coleccion"
    ]
    assert body["datos"][0]["total_productos"] == 4
    assert body["paginacion"]["total"] == 1


def test_colecciones_inactivas_requieren_admin(client: TestClient) -> None:
    response = client.get(
        "/api/colecciones",
        params={"estado": "inactivo"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["codigo"] == "ACCESO_DENEGADO"


def test_obtener_detalle_coleccion(client: TestClient) -> None:
    response = client.get("/api/colecciones/1")

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "la-coleccion"
    assert body["descripcion"] == "Selección especial de temporada."
    assert body["imagen_portada_url"].endswith("la-coleccion.jpg")
    assert body["total_productos"] == 4
    assert "producto_ids" not in body
    assert "productos" not in body
    assert body["creado_en"].endswith("Z")


def test_coleccion_inactiva_no_es_visible_publicamente(
    client: TestClient,
) -> None:
    response = client.get("/api/colecciones/2")

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_crear_coleccion(client: TestClient) -> None:
    response = client.post(
        "/api/colecciones",
        json={
            "nombre": "Verano",
            "descripcion": "Selección de verano.",
            "producto_ids": [1, 4],
        },
    )

    assert response.status_code == 201
    assert response.headers["location"] == "/api/colecciones/3"
    body = response.json()
    assert body["id"] == 3
    assert body["slug"] == "verano"
    assert body["total_productos"] == 2
    assert "producto_ids" not in body
    assert "productos" not in body


def test_crear_coleccion_rechaza_nombre_y_slug_duplicados(
    client: TestClient,
) -> None:
    por_nombre = client.post(
        "/api/colecciones",
        json={"nombre": "La Colección"},
    )
    por_slug = client.post(
        "/api/colecciones",
        json={"nombre": "Otra colección", "slug": "la-coleccion"},
    )

    assert por_nombre.status_code == 409
    assert por_nombre.json()["error"]["detalles"][0]["campo"] == "nombre"
    assert por_slug.status_code == 409
    assert por_slug.json()["error"]["detalles"][0]["campo"] == "slug"


def test_crear_coleccion_rechaza_producto_inexistente(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/colecciones",
        json={"nombre": "Inválida", "producto_ids": [999]},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["codigo"] == "VALIDACION_FALLIDA"
    assert body["error"]["detalles"][0]["campo"] == "producto_ids"


def test_reemplazar_coleccion(client: TestClient) -> None:
    response = client.put(
        "/api/colecciones/1",
        json={
            "nombre": "La Colección",
            "estado": "activo",
            "producto_ids": [1, 2],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "la-coleccion"
    assert body["descripcion"] is None
    assert body["imagen_portada_url"] is None
    assert body["total_productos"] == 2

    productos = client.get(
        "/api/productos",
        params={"coleccion": "la-coleccion"},
    ).json()
    assert [producto["id"] for producto in productos["datos"]] == [2, 1]


def test_reemplazar_coleccion_rechaza_producto_inexistente(
    client: TestClient,
) -> None:
    response = client.put(
        "/api/colecciones/1",
        json={
            "nombre": "La Colección",
            "estado": "activo",
            "producto_ids": [999],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "producto_ids"


def test_eliminar_coleccion_conserva_productos(client: TestClient) -> None:
    response = client.delete("/api/colecciones/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/api/colecciones/1").status_code == 404
    assert client.delete("/api/colecciones/1").status_code == 404
    assert client.get("/api/productos/1").status_code == 200
    assert client.get("/api/productos/1").json()["colecciones"] == []

    productos = client.get(
        "/api/productos",
        params={"coleccion": "la-coleccion"},
    ).json()
    assert productos["paginacion"]["total"] == 0


def test_openapi_incluye_endpoints_de_colecciones(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert "/api/colecciones" in paths
    assert {"get", "post"} <= set(paths["/api/colecciones"])
    assert "/api/colecciones/{coleccion_id}" in paths
    assert {"get", "put", "delete"} <= set(
        paths["/api/colecciones/{coleccion_id}"]
    )
