from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import AppError, register_exception_handlers
from app.schemas.errors import CodigoError, ErrorDetalle, ErrorResponse


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

    @app.get("/error-interno")
    def error_interno() -> None:
        raise RuntimeError("secreto interno")

    @app.get("/error-http-500")
    def error_http_500() -> None:
        raise HTTPException(
            status_code=500,
            detail="detalle sensible que no debe mostrarse",
        )

    @app.get("/error-400")
    def error_400() -> None:
        raise HTTPException(
            status_code=400,
            detail="Mensaje personalizado de solicitud.",
        )

    @app.get("/error-envelope")
    def error_envelope() -> None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "codigo": "RECURSO_NO_ENCONTRADO",
                    "mensaje": "Mensaje preformado.",
                    "detalles": [],
                }
            },
        )

    return app


def validar_estructura_error(body: dict) -> ErrorResponse:
    return ErrorResponse.model_validate(body)


def test_error_de_validacion_usa_envoltura_del_contrato() -> None:
    with TestClient(crear_app()) as client:
        response = client.post("/prueba", json={"precio": "no-es-numero"})

    assert response.status_code == 422
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.VALIDACION_FALLIDA
    assert error.error.detalles[0].campo == "precio"


def test_error_de_aplicacion_usa_codigo_y_detalles() -> None:
    with TestClient(crear_app()) as client:
        response = client.get("/conflicto")

    assert response.status_code == 409
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.CONFLICTO_UNICIDAD
    assert error.error.detalles[0].campo == "sku"


def test_error_500_no_expone_trazas_ni_detalles_internos() -> None:
    with TestClient(crear_app(), raise_server_exceptions=False) as client:
        response = client.get("/error-interno")

    assert response.status_code == 500
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.ERROR_INTERNO
    assert error.error.mensaje == "Ocurrió un error inesperado."
    assert error.error.detalles == []
    assert "secreto interno" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text


def test_error_http_500_no_expone_detail_personalizado() -> None:
    with TestClient(crear_app(), raise_server_exceptions=False) as client:
        response = client.get("/error-http-500")

    assert response.status_code == 500
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.ERROR_INTERNO
    assert error.error.mensaje == "Ocurrió un error inesperado."
    assert "detalle sensible" not in response.text


def test_error_http_400_conserva_mensaje_personalizado() -> None:
    with TestClient(crear_app()) as client:
        response = client.get("/error-400")

    assert response.status_code == 400
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.SOLICITUD_INVALIDA
    assert error.error.mensaje == "Mensaje personalizado de solicitud."


def test_error_http_con_envoltura_preformada_se_respeta() -> None:
    with TestClient(crear_app()) as client:
        response = client.get("/error-envelope")

    assert response.status_code == 404
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.RECURSO_NO_ENCONTRADO
    assert error.error.mensaje == "Mensaje preformado."


def test_error_405_usa_envoltura_uniforme() -> None:
    with TestClient(crear_app()) as client:
        response = client.post("/conflicto")

    assert response.status_code == 405
    error = validar_estructura_error(response.json())
    assert error.error.detalles == []


def test_error_422_de_query_usa_campo_correcto(client: TestClient) -> None:
    response = client.get("/api/productos", params={"pagina": 0})

    assert response.status_code == 422
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.VALIDACION_FALLIDA
    assert error.error.detalles[0].campo == "pagina"


def test_error_422_de_path_usa_campo_correcto(client: TestClient) -> None:
    response = client.get("/api/productos/0")

    assert response.status_code == 422
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.VALIDACION_FALLIDA
    assert error.error.detalles[0].campo == "producto_id"


def test_error_422_de_json_malformado(client: TestClient) -> None:
    response = client.post(
        "/api/productos",
        content="{json-invalido",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    error = validar_estructura_error(response.json())
    assert error.error.codigo == CodigoError.VALIDACION_FALLIDA
