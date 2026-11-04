from fastapi.testclient import TestClient


def test_health_responde_200(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"]
    assert body["version"]
    assert body["environment"]


def test_swagger_disponible(client: TestClient) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_openapi_incluye_health(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/health" in response.json()["paths"]


def test_error_404_usa_envoltura_del_contrato(client: TestClient) -> None:
    response = client.get("/api/recurso-inexistente")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["codigo"] == "RECURSO_NO_ENCONTRADO"
    assert body["error"]["detalles"] == []


def test_cors_permite_origen_configurado(client: TestClient) -> None:
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
