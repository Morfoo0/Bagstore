from typing import Annotated

from pydantic import Field

from app.schemas.common import (
    Estado,
    EstadoFiltro,
    RequestSchema,
    RespuestaLista,
    ResponseSchema,
    SlugOpcional,
    TimestampsResponse,
)

NombreCategoria = Annotated[str, Field(min_length=2, max_length=80)]
DescripcionCategoria = Annotated[str, Field(max_length=1000)]


class CategoriaBase(RequestSchema):
    nombre: NombreCategoria
    descripcion: DescripcionCategoria | None = None
    orden: int = Field(default=0, ge=0)
    estado: Estado = Estado.ACTIVO


class CategoriaCreate(CategoriaBase):
    slug: SlugOpcional = None


class CategoriaUpdate(CategoriaBase):
    estado: Estado
    slug: SlugOpcional = None


class CategoriaResumen(ResponseSchema):
    id: int = Field(gt=0)
    nombre: str
    slug: str


class CategoriaResponse(TimestampsResponse):
    id: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=80)
    slug: str
    descripcion: str | None = Field(default=None, max_length=1000)
    estado: Estado
    orden: int = Field(ge=0)
    total_productos: int = Field(ge=0)


class CategoriaFiltros(RequestSchema):
    nombre: str | None = None
    estado: EstadoFiltro = EstadoFiltro.ACTIVO
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=20, ge=1, le=100)


CategoriaListaResponse = RespuestaLista[CategoriaResponse]
