from fastapi.testclient import TestClient


def test_actualizar_coleccion_actualiza_colecciones_de_productos(
    client: TestClient,
) -> None:
    respuesta = client.put(
        "/api/colecciones/1",
        json={
            "nombre": "La Colección",
            "estado": "activo",
            "producto_ids": [1, 2],
        },
    )
    assert respuesta.status_code == 200

    producto_1 = client.get("/api/productos/1").json()
    producto_2 = client.get("/api/productos/2").json()
    producto_3 = client.get("/api/productos/3").json()

    assert [coleccion["slug"] for coleccion in producto_1["colecciones"]] == [
        "la-coleccion"
    ]
    assert [coleccion["slug"] for coleccion in producto_2["colecciones"]] == [
        "la-coleccion"
    ]
    assert producto_3["colecciones"] == []

    filtrados = client.get(
        "/api/productos",
        params={"coleccion": "la-coleccion"},
    ).json()
    assert [producto["id"] for producto in filtrados["datos"]] == [2, 1]


def test_eliminar_producto_actualiza_coleccion(
    client: TestClient,
) -> None:
    assert client.delete("/api/productos/1").status_code == 204

    coleccion = client.get("/api/colecciones/1").json()
    filtrados = client.get(
        "/api/productos",
        params={"coleccion": "la-coleccion"},
    ).json()

    assert coleccion["total_productos"] == 3
    assert [producto["id"] for producto in filtrados["datos"]] == [8, 6, 3]


def test_eliminar_producto_bloquea_eliminar_categoria(
    client: TestClient,
) -> None:
    assert client.delete("/api/productos/1").status_code == 204

    respuesta = client.delete("/api/categorias/2")
    categoria = client.get("/api/categorias/2").json()

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["codigo"] == "CONFLICTO_DEPENDENCIAS"
    assert categoria["total_productos"] == 3


def test_actualizar_categoria_se_refleja_en_productos(
    client: TestClient,
) -> None:
    respuesta = client.put(
        "/api/categorias/2",
        json={"nombre": "Totes", "estado": "activo"},
    )
    assert respuesta.status_code == 200

    producto = client.get("/api/productos/1").json()
    assert producto["categoria"]["nombre"] == "Totes"
    assert producto["categoria"]["slug"] == "tote-bags"


def test_asociar_producto_nuevo_desde_coleccion(
    client: TestClient,
) -> None:
    creado = client.post(
        "/api/productos",
        json={
            "nombre": "Tote Integración",
            "precio": "100.00",
            "sku": "BAG-INT-001",
            "categoria_id": 2,
            "existencias": 1,
        },
    )
    producto_id = creado.json()["id"]

    respuesta = client.put(
        "/api/colecciones/1",
        json={
            "nombre": "La Colección",
            "estado": "activo",
            "producto_ids": [producto_id],
        },
    )
    producto = client.get(f"/api/productos/{producto_id}").json()
    coleccion = client.get("/api/colecciones/1").json()

    assert respuesta.status_code == 200
    assert [item["slug"] for item in producto["colecciones"]] == [
        "la-coleccion"
    ]
    assert coleccion["total_productos"] == 1


def test_cambiar_estado_producto_actualiza_conteo_categoria(
    client: TestClient,
) -> None:
    respuesta = client.put(
        "/api/productos/2",
        json={
            "nombre": "Tote Bag Oliva",
            "precio": "749.00",
            "categoria_id": 2,
            "existencias": 0,
            "imagenes": [],
            "estado": "inactivo",
        },
    )
    assert respuesta.status_code == 200

    categoria = client.get("/api/categorias/2").json()
    assert categoria["total_productos"] == 3
