from typing import Annotated

from pydantic import AfterValidator, Field

from app.schemas.common import (
    MAX_PRODUCTOS_COLECCION,
    Estado,
    EstadoFiltro,
    RequestSchema,
    RespuestaLista,
    ResponseSchema,
    SlugOpcional,
    TimestampsResponse,
    UrlHttpOpcional,
)

NombreColeccion = Annotated[str, Field(min_length=2, max_length=100)]
DescripcionColeccion = Annotated[str, Field(max_length=2000)]


def _validar_producto_ids(valor: list[int] | None) -> list[int] | None:
    if valor is None:
        return None
    if len(valor) > MAX_PRODUCTOS_COLECCION:
        raise ValueError(
            f"No se permiten más de {MAX_PRODUCTOS_COLECCION} productos por colección."
        )
    if len(set(valor)) != len(valor):
        raise ValueError("La lista 'producto_ids' no puede contener duplicados.")
    if any(identificador <= 0 for identificador in valor):
        raise ValueError("Todos los 'producto_ids' deben ser enteros positivos.")
    return valor


ProductoIds = Annotated[list[int], AfterValidator(_validar_producto_ids)]
ProductoIdsOpcional = Annotated[
    list[int] | None, AfterValidator(_validar_producto_ids)
]


class ColeccionBase(RequestSchema):
    nombre: NombreColeccion
    descripcion: DescripcionColeccion | None = None
    estado: Estado = Estado.ACTIVO
    imagen_portada_url: UrlHttpOpcional = None


class ColeccionCreate(ColeccionBase):
    slug: SlugOpcional = None
    producto_ids: ProductoIdsOpcional = None


class ColeccionUpdate(ColeccionBase):
    estado: Estado
    producto_ids: ProductoIds
    slug: SlugOpcional = None


class ColeccionResumen(ResponseSchema):
    id: int = Field(gt=0)
    nombre: str
    slug: str


class ColeccionResponse(TimestampsResponse):
    id: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=100)
    slug: str
    descripcion: str | None = Field(default=None, max_length=2000)
    estado: Estado
    imagen_portada_url: str | None = Field(default=None, max_length=500)
    total_productos: int = Field(ge=0)


class ColeccionFiltros(RequestSchema):
    nombre: str | None = None
    estado: EstadoFiltro = EstadoFiltro.ACTIVO
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=20, ge=1, le=100)


ColeccionListaResponse = RespuestaLista[ColeccionResponse]
