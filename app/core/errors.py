import logging
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.errors import CodigoError, ErrorBody, ErrorDetalle, ErrorResponse

logger = logging.getLogger(__name__)

CODIGOS_POR_ESTADO = {
    400: CodigoError.SOLICITUD_INVALIDA,
    401: CodigoError.NO_AUTENTICADO,
    403: CodigoError.ACCESO_DENEGADO,
    404: CodigoError.RECURSO_NO_ENCONTRADO,
    409: CodigoError.CONFLICTO_DEPENDENCIAS,
    422: CodigoError.VALIDACION_FALLIDA,
    500: CodigoError.ERROR_INTERNO,
}

MENSAJES_POR_ESTADO = {
    400: "La solicitud contiene parámetros inválidos.",
    401: "Se requieren credenciales válidas para realizar esta operación.",
    403: "Se requiere el rol administrador para realizar esta operación.",
    404: "No se encontró el recurso solicitado.",
    409: "La solicitud entra en conflicto con el estado actual del recurso.",
    422: "Los datos enviados no son válidos.",
    500: "Ocurrió un error inesperado.",
}


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        codigo: CodigoError,
        mensaje: str,
        detalles: Sequence[ErrorDetalle] | None = None,
    ) -> None:
        self.status_code = status_code
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = list(detalles or [])
        super().__init__(mensaje)


def _respuesta_error(
    status_code: int,
    codigo: CodigoError,
    mensaje: str,
    detalles: Sequence[ErrorDetalle] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(
            codigo=codigo,
            mensaje=mensaje,
            detalles=list(detalles or []),
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


def _campo_desde_loc(loc: Sequence[Any]) -> str:
    partes = [
        str(parte)
        for parte in loc
        if parte not in {"body", "query", "path", "header", "cookie"}
    ]
    return ".".join(partes) if partes else "cuerpo"


def _mensaje_validacion(mensaje: str) -> str:
    for prefijo in ("Value error, ", "Assertion failed, "):
        if mensaje.startswith(prefijo):
            return mensaje[len(prefijo) :]
    return mensaje


async def _manejar_error_aplicacion(
    request: Request, exc: AppError
) -> JSONResponse:
    return _respuesta_error(
        status_code=exc.status_code,
        codigo=exc.codigo,
        mensaje=exc.mensaje,
        detalles=exc.detalles,
    )


async def _manejar_error_validacion(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    detalles = [
        ErrorDetalle(
            campo=_campo_desde_loc(error.get("loc", ())),
            mensaje=_mensaje_validacion(
                str(error.get("msg", "Valor inválido."))
            ),
        )
        for error in exc.errors()
    ]
    return _respuesta_error(
        status_code=422,
        codigo=CodigoError.VALIDACION_FALLIDA,
        mensaje=MENSAJES_POR_ESTADO[422],
        detalles=detalles,
    )


async def _manejar_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if exc.status_code >= 500:
        return _respuesta_error(
            status_code=exc.status_code,
            codigo=CodigoError.ERROR_INTERNO,
            mensaje=MENSAJES_POR_ESTADO[500],
        )

    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    codigo = CODIGOS_POR_ESTADO.get(exc.status_code)
    if codigo is None:
        codigo = (
            CodigoError.SOLICITUD_INVALIDA
            if exc.status_code < 500
            else CodigoError.ERROR_INTERNO
        )

    mensaje = MENSAJES_POR_ESTADO.get(
        exc.status_code, "La solicitud no pudo completarse."
    )
    if (
        isinstance(exc.detail, str)
        and exc.detail
        and exc.detail not in {"Not Found", "Method Not Allowed"}
    ):
        mensaje = exc.detail

    return _respuesta_error(
        status_code=exc.status_code,
        codigo=codigo,
        mensaje=mensaje,
    )


async def _manejar_error_no_controlado(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.error(
        "Error no controlado en %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return _respuesta_error(
        status_code=500,
        codigo=CodigoError.ERROR_INTERNO,
        mensaje=MENSAJES_POR_ESTADO[500],
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _manejar_error_aplicacion)
    app.add_exception_handler(RequestValidationError, _manejar_error_validacion)
    app.add_exception_handler(StarletteHTTPException, _manejar_http_exception)
    app.add_exception_handler(Exception, _manejar_error_no_controlado)
