import re
from typing import Annotated

from pydantic import AfterValidator, Field, field_validator

from app.schemas.common import (
    RequestSchema,
    RespuestaLista,
    ResponseSchema,
    TimestampsResponse,
)

TONO_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
NombreColor = Annotated[str, Field(min_length=2, max_length=50)]


def _validar_tono(valor: str) -> str:
    tono = valor.strip().upper()
    if not TONO_PATTERN.fullmatch(tono):
        raise ValueError("El tono debe tener el formato hexadecimal #RRGGBB.")
    return tono


Tono = Annotated[str, AfterValidator(_validar_tono)]


def _validar_color_ids(valor: list[int]) -> list[int]:
    if len(set(valor)) != len(valor):
        raise ValueError("La lista 'color_ids' no puede contener duplicados.")
    if any(color_id <= 0 for color_id in valor):
        raise ValueError("Todos los 'color_ids' deben ser enteros positivos.")
    return valor


ColorIds = Annotated[list[int], AfterValidator(_validar_color_ids)]


class ColorCreate(RequestSchema):
    nombre: NombreColor
    tono: Tono


class ColorUpdate(RequestSchema):
    nombre: NombreColor
    tono: Tono


class ColorResumen(ResponseSchema):
    id: int = Field(gt=0)
    nombre: str
    tono: str


class ColorResponse(TimestampsResponse):
    id: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=50)
    tono: str = Field(min_length=7, max_length=7)

    @field_validator("tono")
    @classmethod
    def _normalizar_tono_respuesta(cls, valor: str) -> str:
        return valor.upper()


class ColorFiltros(RequestSchema):
    nombre: str | None = None
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=20, ge=1, le=100)


class ColoresProductoResponse(ResponseSchema):
    datos: list[ColorResumen]


class ProductoColoresUpdate(RequestSchema):
    color_ids: ColorIds


ColorListaResponse = RespuestaLista[ColorResponse]
