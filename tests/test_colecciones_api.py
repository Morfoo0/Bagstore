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


def test_obtener_coleccion_inexistente(client: TestClient) -> None:
    response = client.get("/api/colecciones/999")

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_actualizar_coleccion_inexistente(client: TestClient) -> None:
    response = client.put(
        "/api/colecciones/999",
        json={
            "nombre": "Inexistente",
            "estado": "activo",
            "producto_ids": [],
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_eliminar_coleccion_inexistente(client: TestClient) -> None:
    response = client.delete("/api/colecciones/999")

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_paginacion_de_colecciones(client: TestClient) -> None:
    assert client.post(
        "/api/colecciones",
        json={"nombre": "Verano"},
    ).status_code == 201

    response = client.get(
        "/api/colecciones",
        params={"pagina": 2, "por_pagina": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert [coleccion["slug"] for coleccion in body["datos"]] == ["verano"]
    assert body["paginacion"] == {
        "pagina": 2,
        "por_pagina": 1,
        "total": 2,
        "total_paginas": 2,
    }


def test_filtrar_colecciones_por_nombre(client: TestClient) -> None:
    response = client.get(
        "/api/colecciones",
        params={"nombre": "coleccion"},
    )

    assert response.status_code == 200
    assert [coleccion["slug"] for coleccion in response.json()["datos"]] == [
        "la-coleccion"
    ]


def test_crear_coleccion_sin_producto_ids(client: TestClient) -> None:
    response = client.post(
        "/api/colecciones",
        json={"nombre": "Vacía"},
    )

    assert response.status_code == 201
    assert response.json()["total_productos"] == 0


def test_actualizar_coleccion_exige_estado_y_producto_ids(
    client: TestClient,
) -> None:
    response = client.put(
        "/api/colecciones/1",
        json={"nombre": "La Colección"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["codigo"] == "VALIDACION_FALLIDA"
    campos = {detalle["campo"] for detalle in body["error"]["detalles"]}
    assert {"estado", "producto_ids"} <= campos


def test_crear_coleccion_rechaza_producto_ids_duplicados(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/colecciones",
        json={"nombre": "Duplicada", "producto_ids": [1, 1]},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["detalles"][0]["campo"] == "producto_ids"


def test_crear_coleccion_rechaza_url_invalida(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/colecciones",
        json={
            "nombre": "URL inválida",
            "imagen_portada_url": "ftp://cdn.bagstore.com/portada.jpg",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["detalles"][0]["campo"] == "imagen_portada_url"


def test_crear_coleccion_rechaza_campos_desconocidos(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/colecciones",
        json={"nombre": "Con extra", "campo_extra": "no permitido"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["detalles"][0]["campo"] == "campo_extra"


def test_coleccion_inactiva_no_es_visible_publicamente(
    client: TestClient,
) -> None:
    creada = client.post(
        "/api/colecciones",
        json={"nombre": "Archivada", "estado": "inactivo"},
    )
    coleccion_id = creada.json()["id"]

    detalle = client.get(f"/api/colecciones/{coleccion_id}")
    listado = client.get("/api/colecciones").json()

    assert creada.status_code == 201
    assert detalle.status_code == 404
    assert coleccion_id not in [
        coleccion["id"] for coleccion in listado["datos"]
    ]


def test_crear_coleccion_con_slug_explicito(client: TestClient) -> None:
    response = client.post(
        "/api/colecciones",
        json={"nombre": "Verano", "slug": "verano-2027"},
    )

    assert response.status_code == 201
    assert response.json()["slug"] == "verano-2027"


def test_actualizar_coleccion_con_slug_nuevo(client: TestClient) -> None:
    response = client.put(
        "/api/colecciones/1",
        json={
            "nombre": "La Colección",
            "slug": "la-coleccion-2027",
            "estado": "activo",
            "producto_ids": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "la-coleccion-2027"


def test_crear_coleccion_rechaza_slug_no_generable(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/colecciones",
        json={"nombre": "!!"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "slug"
