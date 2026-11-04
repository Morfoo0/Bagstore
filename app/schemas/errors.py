from enum import Enum

from pydantic import BaseModel, Field


class CodigoError(str, Enum):
    SOLICITUD_INVALIDA = "SOLICITUD_INVALIDA"
    NO_AUTENTICADO = "NO_AUTENTICADO"
    ACCESO_DENEGADO = "ACCESO_DENEGADO"
    RECURSO_NO_ENCONTRADO = "RECURSO_NO_ENCONTRADO"
    CONFLICTO_UNICIDAD = "CONFLICTO_UNICIDAD"
    CONFLICTO_DEPENDENCIAS = "CONFLICTO_DEPENDENCIAS"
    VALIDACION_FALLIDA = "VALIDACION_FALLIDA"
    ERROR_INTERNO = "ERROR_INTERNO"


class ErrorDetalle(BaseModel):
    campo: str
    mensaje: str


class ErrorBody(BaseModel):
    codigo: CodigoError
    mensaje: str
    detalles: list[ErrorDetalle] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody
