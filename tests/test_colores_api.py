from fastapi.testclient import TestClient


def crear_color(
    client: TestClient,
    nombre: str = "Rojo",
    tono: str = "#FF0000",
) -> dict:
    response = client.post(
        "/api/colores",
        json={"nombre": nombre, "tono": tono},
    )
    assert response.status_code == 201
    return response.json()


def test_listar_colores_vacio(client: TestClient) -> None:
    response = client.get("/api/colores")

    assert response.status_code == 200
    assert response.json() == {
        "datos": [],
        "paginacion": {
            "pagina": 1,
            "por_pagina": 20,
            "total": 0,
            "total_paginas": 0,
        },
    }


def test_crear_color_normaliza_tono(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/api/colores",
        json={"nombre": "  Verde oliva  ", "tono": "#556b2f"},
    )

    assert response.status_code == 201
    assert response.headers["location"] == "/api/colores/1"
    body = response.json()
    assert body["nombre"] == "Verde oliva"
    assert body["tono"] == "#556B2F"
    assert body["id"] == 1


def test_color_duplicado_ignora_mayusculas(admin_client: TestClient) -> None:
    crear_color(admin_client, "Rojo")

    response = admin_client.post(
        "/api/colores",
        json={"nombre": "rojo", "tono": "#FF0000"},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["codigo"] == "CONFLICTO_UNICIDAD"
    assert body["error"]["detalles"][0]["campo"] == "nombre"


def test_color_rechaza_tono_invalido(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/api/colores",
        json={"nombre": "Rojo", "tono": "rojo"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["codigo"] == "VALIDACION_FALLIDA"
    assert body["error"]["detalles"][0]["campo"] == "tono"


def test_actualizar_color(admin_client: TestClient) -> None:
    color = crear_color(admin_client, "Rojo", "#FF0000")

    response = admin_client.put(
        f"/api/colores/{color['id']}",
        json={"nombre": "Rojo coral", "tono": "#FF4040"},
    )

    assert response.status_code == 200
    assert response.json()["nombre"] == "Rojo coral"
    assert response.json()["tono"] == "#FF4040"


def test_actualizar_color_rechaza_duplicado(
    admin_client: TestClient,
) -> None:
    crear_color(admin_client, "Rojo")
    azul = crear_color(admin_client, "Azul", "#0000FF")

    response = admin_client.put(
        f"/api/colores/{azul['id']}",
        json={"nombre": "rojo", "tono": "#0000FF"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["detalles"][0]["campo"] == "nombre"


def test_eliminar_color_sin_productos(admin_client: TestClient) -> None:
    color = crear_color(admin_client)

    response = admin_client.delete(f"/api/colores/{color['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert admin_client.get(f"/api/colores/{color['id']}").status_code == 404


def test_eliminar_color_con_productos_devuelve_409(
    admin_client: TestClient,
) -> None:
    color = crear_color(admin_client)
    assert admin_client.put(
        "/api/productos/1/colores",
        json={"color_ids": [color["id"]]},
    ).status_code == 200

    response = admin_client.delete(f"/api/colores/{color['id']}")

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "CONFLICTO_DEPENDENCIAS"


def test_asociar_colores_y_filtrar_productos(
    admin_client: TestClient,
    public_client: TestClient,
) -> None:
    rojo = crear_color(admin_client, "Rojo", "#FF0000")
    azul = crear_color(admin_client, "Azul", "#0000FF")
    assert admin_client.put(
        "/api/productos/1/colores",
        json={"color_ids": [rojo["id"], azul["id"]]},
    ).status_code == 200
    assert admin_client.put(
        "/api/productos/2/colores",
        json={"color_ids": [rojo["id"]]},
    ).status_code == 200

    producto = public_client.get("/api/productos/1/colores")
    filtrados = public_client.get(
        "/api/productos",
        params={"color_id": rojo["id"]},
    )

    assert producto.status_code == 200
    assert {color["nombre"] for color in producto.json()["datos"]} == {
        "Rojo",
        "Azul",
    }
    assert [item["id"] for item in filtrados.json()["datos"]] == [2, 1]


def test_reemplazar_colores_no_elimina_productos_ni_colores(
    admin_client: TestClient,
    public_client: TestClient,
) -> None:
    rojo = crear_color(admin_client, "Rojo", "#FF0000")
    azul = crear_color(admin_client, "Azul", "#0000FF")
    admin_client.put(
        "/api/productos/1/colores",
        json={"color_ids": [rojo["id"], azul["id"]]},
    )

    response = admin_client.put(
        "/api/productos/1/colores",
        json={"color_ids": [azul["id"]]},
    )

    assert response.status_code == 200
    assert [color["id"] for color in response.json()["datos"]] == [azul["id"]]
    assert public_client.get("/api/productos/1").status_code == 200
    assert admin_client.delete(f"/api/colores/{rojo['id']}").status_code == 204
    assert admin_client.delete(f"/api/colores/{azul['id']}").status_code == 409


def test_color_de_producto_inactivo_solo_admin(
    admin_client: TestClient,
    public_client: TestClient,
) -> None:
    color = crear_color(admin_client)
    assert admin_client.put(
        "/api/productos/4/colores",
        json={"color_ids": [color["id"]]},
    ).status_code == 200

    publico = public_client.get(
        "/api/productos",
        params={"color_id": color["id"]},
    )
    admin = admin_client.get(
        "/api/productos",
        params={"color_id": color["id"], "estado": "todos"},
    )

    assert public_client.get("/api/productos/4/colores").status_code == 404
    assert admin_client.get("/api/productos/4/colores").status_code == 200
    assert publico.json()["paginacion"]["total"] == 0
    assert admin.json()["paginacion"]["total"] == 1


def test_asociar_color_inexistente_devuelve_422(
    admin_client: TestClient,
) -> None:
    response = admin_client.put(
        "/api/productos/1/colores",
        json={"color_ids": [999]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "color_ids"


def test_escrituras_de_colores_requieren_admin(
    public_client: TestClient,
    cliente_client: TestClient,
) -> None:
    publico = public_client.post(
        "/api/colores",
        json={"nombre": "Público", "tono": "#FFFFFF"},
    )
    cliente = cliente_client.post(
        "/api/colores",
        json={"nombre": "Cliente", "tono": "#FFFFFF"},
    )

    assert publico.status_code == 401
    assert cliente.status_code == 403


def test_filtrar_colores_por_nombre(admin_client: TestClient) -> None:
    crear_color(admin_client, "Rojo", "#FF0000")
    crear_color(admin_client, "Azul", "#0000FF")

    response = admin_client.get(
        "/api/colores",
        params={"nombre": "roj"},
    )

    assert response.status_code == 200
    assert [color["nombre"] for color in response.json()["datos"]] == ["Rojo"]


def test_color_inexistente_devuelve_404(admin_client: TestClient) -> None:
    response = admin_client.get("/api/colores/999")

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"
