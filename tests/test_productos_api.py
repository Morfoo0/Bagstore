from fastapi.testclient import TestClient


def datos_producto(**overrides) -> dict:
    datos = {
        "nombre": "Tote Nueva",
        "precio": "123.45",
        "sku": "BAG-NEW-001",
        "categoria_id": 2,
        "existencias": 4,
    }
    datos.update(overrides)
    return datos


def datos_actualizacion(**overrides) -> dict:
    datos = {
        "nombre": "Tote Bag Aurora",
        "precio": "950.00",
        "categoria_id": 2,
        "existencias": 0,
        "imagenes": [],
        "estado": "activo",
    }
    datos.update(overrides)
    return datos


def test_listar_productos_publicos(client: TestClient) -> None:
    response = client.get("/api/productos")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"datos", "paginacion"}
    assert body["paginacion"] == {
        "pagina": 1,
        "por_pagina": 20,
        "total": 8,
        "total_paginas": 1,
    }
    assert body["datos"][0]["id"] == 10
    assert body["datos"][0]["precio"] == 849.0
    assert "sku" not in body["datos"][0]
    assert body["datos"][0]["categoria"]["slug"] == "tote-bags"


def test_filtrar_por_categoria_disponibilidad_y_orden(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/productos",
        params={
            "categoria": "tote-bags",
            "disponible": "true",
            "orden": "precio_asc",
        },
    )

    assert response.status_code == 200
    datos = response.json()["datos"]
    assert [producto["id"] for producto in datos] == [7, 10, 1]


def test_filtrar_por_coleccion(client: TestClient) -> None:
    response = client.get(
        "/api/productos",
        params={"coleccion": "la-coleccion"},
    )

    assert response.status_code == 200
    datos = response.json()["datos"]
    assert [producto["id"] for producto in datos] == [8, 6, 3, 1]


def test_paginacion(client: TestClient) -> None:
    response = client.get(
        "/api/productos",
        params={"pagina": 2, "por_pagina": 3},
    )

    body = response.json()
    assert response.status_code == 200
    assert [producto["id"] for producto in body["datos"]] == [6, 5, 3]
    assert body["paginacion"]["total"] == 8
    assert body["paginacion"]["total_paginas"] == 3


def test_ordenar_por_precio_descendente(client: TestClient) -> None:
    response = client.get(
        "/api/productos",
        params={"orden": "precio_desc"},
    )

    datos = response.json()["datos"]
    assert datos[0]["id"] == 3
    assert datos[-1]["id"] == 5


def test_obtener_detalle_de_producto(client: TestClient) -> None:
    response = client.get("/api/productos/1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["sku"] == "BAG-TOT-001"
    assert body["categoria"] == {
        "id": 2,
        "nombre": "Tote Bags",
        "slug": "tote-bags",
    }
    assert [coleccion["slug"] for coleccion in body["colecciones"]] == [
        "la-coleccion"
    ]
    assert len(body["imagenes"]) == 2
    assert body["imagenes"][0]["es_principal"] is True
    assert body["disponible"] is True
    assert body["creado_en"].endswith("Z")


def test_producto_inactivo_no_es_visible_publicamente(
    client: TestClient,
) -> None:
    detalle = client.get("/api/productos/4")
    listado = client.get(
        "/api/productos",
        params={"estado": "inactivo"},
    )

    assert detalle.status_code == 404
    assert detalle.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"
    assert listado.status_code == 403
    assert listado.json()["error"]["codigo"] == "ACCESO_DENEGADO"


def test_filtros_incompatibles_devuelven_400(client: TestClient) -> None:
    response = client.get(
        "/api/productos",
        params={"categoria": "tote-bags", "categoria_id": 2},
    )

    assert response.status_code == 400
    assert response.json()["error"]["codigo"] == "SOLICITUD_INVALIDA"


def test_crear_producto_devuelve_201_y_location(
    client: TestClient,
) -> None:
    response = client.post("/api/productos", json=datos_producto())

    assert response.status_code == 201
    assert response.headers["location"] == "/api/productos/11"
    body = response.json()
    assert body["id"] == 11
    assert body["slug"] == "tote-nueva"
    assert body["disponible"] is True
    assert body["colecciones"] == []
    assert client.get("/api/productos/11").status_code == 200


def test_crear_producto_rechaza_sku_duplicado(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/productos",
        json=datos_producto(sku="BAG-TOT-001"),
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["codigo"] == "CONFLICTO_UNICIDAD"
    assert body["error"]["detalles"][0]["campo"] == "sku"


def test_crear_producto_rechaza_slug_duplicado(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/productos",
        json=datos_producto(
            sku="BAG-NEW-002",
            slug="tote-bag-aurora",
        ),
    )

    assert response.status_code == 409
    assert response.json()["error"]["detalles"][0]["campo"] == "slug"


def test_crear_producto_valida_body(client: TestClient) -> None:
    response = client.post(
        "/api/productos",
        json=datos_producto(precio="0"),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["codigo"] == "VALIDACION_FALLIDA"
    assert body["error"]["detalles"][0]["campo"] == "precio"


def test_crear_producto_rechaza_categoria_inexistente(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/productos",
        json=datos_producto(categoria_id=999),
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "categoria_id"


def test_reemplazar_producto(client: TestClient) -> None:
    response = client.put(
        "/api/productos/1",
        json=datos_actualizacion(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nombre"] == "Tote Bag Aurora"
    assert body["slug"] == "tote-bag-aurora"
    assert body["descripcion"] is None
    assert body["imagenes"] == []
    assert body["existencias"] == 0
    assert body["disponible"] is False
    assert [coleccion["slug"] for coleccion in body["colecciones"]] == [
        "la-coleccion"
    ]


def test_reemplazar_producto_rechaza_cambio_de_sku(
    client: TestClient,
) -> None:
    response = client.put(
        "/api/productos/1",
        json=datos_actualizacion(sku="BAG-TOT-999"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "sku"


def test_eliminar_producto_y_reservar_sku_slug(
    client: TestClient,
) -> None:
    response = client.delete("/api/productos/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/api/productos/1").status_code == 404
    assert client.delete("/api/productos/1").status_code == 404
    assert client.get("/api/productos").json()["paginacion"]["total"] == 7

    response = client.post(
        "/api/productos",
        json=datos_producto(
            sku="BAG-NEW-003",
            slug="tote-bag-aurora",
        ),
    )
    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "CONFLICTO_UNICIDAD"


def test_openapi_incluye_endpoints_de_productos(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert "/api/productos" in paths
    assert {"get", "post"} <= set(paths["/api/productos"])
    assert "/api/productos/{producto_id}" in paths
    assert {"get", "put", "delete"} <= set(
        paths["/api/productos/{producto_id}"]
    )
