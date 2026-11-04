from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import AppError, register_exception_handlers
from app.schemas.errors import CodigoError, ErrorDetalle


class CuerpoPrueba(BaseModel):
    precio: int


def crear_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/prueba")
    def prueba(cuerpo: CuerpoPrueba) -> CuerpoPrueba:
        return cuerpo

    @app.get("/conflicto")
    def conflicto() -> None:
        raise AppError(
            409,
            CodigoError.CONFLICTO_UNICIDAD,
            "Ya existe un producto con el SKU indicado.",
            [ErrorDetalle(campo="sku", mensaje="El SKU ya está registrado.")],
        )

    return app


def test_error_de_validacion_usa_envoltura_del_contrato() -> None:
    with TestClient(crear_app()) as client:
        response = client.post("/prueba", json={"precio": "no-es-numero"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["codigo"] == "VALIDACION_FALLIDA"
    assert body["error"]["detalles"][0]["campo"] == "precio"


def test_error_de_aplicacion_usa_codigo_y_detalles() -> None:
    with TestClient(crear_app()) as client:
        response = client.get("/conflicto")

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["codigo"] == "CONFLICTO_UNICIDAD"
    assert body["error"]["detalles"][0]["campo"] == "sku"
