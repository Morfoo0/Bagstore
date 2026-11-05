from fastapi.testclient import TestClient


def test_listar_categorias_publicas(client: TestClient) -> None:
    response = client.get("/api/categorias")

    assert response.status_code == 200
    body = response.json()
    assert [categoria["id"] for categoria in body["datos"]] == [2, 1, 3]
    assert [categoria["total_productos"] for categoria in body["datos"]] == [
        4,
        2,
        2,
    ]
    assert body["paginacion"] == {
        "pagina": 1,
        "por_pagina": 20,
        "total": 3,
        "total_paginas": 1,
    }


def test_filtrar_categorias_por_nombre(client: TestClient) -> None:
    response = client.get("/api/categorias", params={"nombre": "tote"})

    assert response.status_code == 200
    assert [categoria["slug"] for categoria in response.json()["datos"]] == [
        "tote-bags"
    ]


def test_categorias_inactivas_requieren_admin(client: TestClient) -> None:
    response = client.get(
        "/api/categorias",
        params={"estado": "inactivo"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["codigo"] == "ACCESO_DENEGADO"


def test_obtener_detalle_categoria(client: TestClient) -> None:
    response = client.get("/api/categorias/2")

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "tote-bags"
    assert body["descripcion"] == "Bolsas tote."
    assert body["orden"] == 1
    assert body["total_productos"] == 4
    assert body["creado_en"].endswith("Z")


def test_crear_categoria(client: TestClient) -> None:
    response = client.post(
        "/api/categorias",
        json={"nombre": "Bandoleras", "descripcion": "Bolsas bandolera."},
    )

    assert response.status_code == 201
    assert response.headers["location"] == "/api/categorias/4"
    body = response.json()
    assert body["id"] == 4
    assert body["slug"] == "bandoleras"
    assert body["estado"] == "activo"
    assert body["orden"] == 0
    assert body["total_productos"] == 0


def test_crear_categoria_rechaza_nombre_y_slug_duplicados(
    client: TestClient,
) -> None:
    por_nombre = client.post(
        "/api/categorias",
        json={"nombre": "Tote Bags"},
    )
    por_slug = client.post(
        "/api/categorias",
        json={"nombre": "Otra Tote", "slug": "tote-bags"},
    )

    assert por_nombre.status_code == 409
    assert por_nombre.json()["error"]["detalles"][0]["campo"] == "nombre"
    assert por_slug.status_code == 409
    assert por_slug.json()["error"]["detalles"][0]["campo"] == "slug"


def test_crear_categoria_valida_body(client: TestClient) -> None:
    response = client.post(
        "/api/categorias",
        json={"nombre": "A"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["codigo"] == "VALIDACION_FALLIDA"
    assert body["error"]["detalles"][0]["campo"] == "nombre"


def test_reemplazar_categoria(client: TestClient) -> None:
    response = client.put(
        "/api/categorias/1",
        json={"nombre": "Cross Body Premium", "estado": "activo"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nombre"] == "Cross Body Premium"
    assert body["slug"] == "cross-body"
    assert body["descripcion"] is None
    assert body["orden"] == 0
    assert body["total_productos"] == 3


def test_desactivar_categoria_con_productos_devuelve_409(
    client: TestClient,
) -> None:
    response = client.put(
        "/api/categorias/2",
        json={"nombre": "Tote Bags", "estado": "inactivo"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "CONFLICTO_DEPENDENCIAS"


def test_eliminar_categoria_con_productos_devuelve_409(
    client: TestClient,
) -> None:
    response = client.delete("/api/categorias/2")

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "CONFLICTO_DEPENDENCIAS"


def test_crear_y_eliminar_categoria_vacia(client: TestClient) -> None:
    creada = client.post(
        "/api/categorias",
        json={"nombre": "Temporal"},
    )
    categoria_id = creada.json()["id"]

    eliminada = client.delete(f"/api/categorias/{categoria_id}")

    assert eliminada.status_code == 204
    assert eliminada.content == b""
    assert client.get(f"/api/categorias/{categoria_id}").status_code == 404
    assert client.delete(f"/api/categorias/{categoria_id}").status_code == 404


def test_openapi_incluye_endpoints_de_categorias(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert "/api/categorias" in paths
    assert {"get", "post"} <= set(paths["/api/categorias"])
    assert "/api/categorias/{categoria_id}" in paths
    assert {"get", "put", "delete"} <= set(
        paths["/api/categorias/{categoria_id}"]
    )


def test_obtener_categoria_inexistente(client: TestClient) -> None:
    response = client.get("/api/categorias/999")

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_actualizar_categoria_inexistente(client: TestClient) -> None:
    response = client.put(
        "/api/categorias/999",
        json={"nombre": "Inexistente", "estado": "activo"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_eliminar_categoria_inexistente(client: TestClient) -> None:
    response = client.delete("/api/categorias/999")

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_paginacion_de_categorias(client: TestClient) -> None:
    response = client.get(
        "/api/categorias",
        params={"pagina": 2, "por_pagina": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert [categoria["id"] for categoria in body["datos"]] == [1]
    assert body["paginacion"] == {
        "pagina": 2,
        "por_pagina": 1,
        "total": 3,
        "total_paginas": 3,
    }


def test_categoria_inactiva_no_es_visible_publicamente(
    client: TestClient,
) -> None:
    creada = client.post(
        "/api/categorias",
        json={"nombre": "Archivada", "estado": "inactivo"},
    )
    categoria_id = creada.json()["id"]

    detalle = client.get(f"/api/categorias/{categoria_id}")
    listado = client.get("/api/categorias").json()

    assert creada.status_code == 201
    assert detalle.status_code == 404
    assert categoria_id not in [
        categoria["id"] for categoria in listado["datos"]
    ]


def test_actualizar_categoria_rechaza_slug_duplicado(
    client: TestClient,
) -> None:
    response = client.put(
        "/api/categorias/1",
        json={
            "nombre": "Cross Body",
            "slug": "tote-bags",
            "estado": "activo",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["detalles"][0]["campo"] == "slug"


def test_crear_categoria_rechaza_orden_negativo(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/categorias",
        json={"nombre": "Orden inválido", "orden": -1},
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "orden"


def test_crear_categoria_rechaza_campos_desconocidos(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/categorias",
        json={"nombre": "Con extra", "campo_extra": "no permitido"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "campo_extra"


def test_crear_categoria_con_slug_explicito(client: TestClient) -> None:
    response = client.post(
        "/api/categorias",
        json={"nombre": "Bandoleras", "slug": "bandoleras-premium"},
    )

    assert response.status_code == 201
    assert response.json()["slug"] == "bandoleras-premium"


def test_actualizar_categoria_con_slug_nuevo(client: TestClient) -> None:
    response = client.put(
        "/api/categorias/1",
        json={
            "nombre": "Cross Body",
            "slug": "cross-body-premium",
            "estado": "activo",
        },
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "cross-body-premium"


def test_crear_categoria_rechaza_slug_no_generable(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/categorias",
        json={"nombre": "!!"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "slug"
