from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BeforeValidator, Field, field_serializer, field_validator

from app.schemas.categoria import CategoriaResumen
from app.schemas.coleccion import ColeccionResumen
from app.schemas.common import (
    MAX_IMAGENES,
    SKU_PATTERN,
    Estado,
    EstadoFiltro,
    Existencias,
    Precio,
    RequestSchema,
    RespuestaLista,
    ResponseSchema,
    SlugOpcional,
    TimestampsResponse,
    normalizar_sku,
    serializar_precio,
)
from app.schemas.imagen import ImagenCreate, ImagenResponse, normalizar_imagenes

NombreProducto = Annotated[str, Field(min_length=2, max_length=150)]
DescripcionProducto = Annotated[str, Field(max_length=5000)]


class OrdenProducto(str, Enum):
    RECIENTE = "reciente"
    NOMBRE_ASC = "nombre_asc"
    NOMBRE_DESC = "nombre_desc"
    PRECIO_ASC = "precio_asc"
    PRECIO_DESC = "precio_desc"


def _validar_sku(valor: str | None) -> str | None:
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError("El SKU debe ser texto.")
    sku = normalizar_sku(valor)
    if not 3 <= len(sku) <= 50:
        raise ValueError("El SKU debe tener entre 3 y 50 caracteres.")
    if not SKU_PATTERN.fullmatch(sku):
        raise ValueError(
            "El SKU solo admite mayúsculas, números y guiones simples."
        )
    return sku


Sku = Annotated[str, BeforeValidator(_validar_sku)]
SkuOpcional = Annotated[str | None, BeforeValidator(_validar_sku)]


class ProductoCreate(RequestSchema):
    nombre: NombreProducto
    slug: SlugOpcional = None
    descripcion: DescripcionProducto | None = None
    precio: Precio
    sku: Sku
    categoria_id: int = Field(gt=0)
    existencias: Existencias
    imagenes: list[ImagenCreate] = Field(
        default_factory=list, max_length=MAX_IMAGENES
    )
    estado: Estado = Estado.ACTIVO

    @field_validator("imagenes")
    @classmethod
    def _normalizar_lista_imagenes(
        cls, imagenes: list[ImagenCreate]
    ) -> list[ImagenCreate]:
        return normalizar_imagenes(imagenes)


class ProductoUpdate(RequestSchema):
    nombre: NombreProducto
    slug: SlugOpcional = None
    descripcion: DescripcionProducto | None = None
    precio: Precio
    sku: SkuOpcional = None
    categoria_id: int = Field(gt=0)
    existencias: Existencias
    imagenes: list[ImagenCreate] = Field(..., max_length=MAX_IMAGENES)
    estado: Estado

    @field_validator("imagenes")
    @classmethod
    def _normalizar_lista_imagenes(
        cls, imagenes: list[ImagenCreate]
    ) -> list[ImagenCreate]:
        return normalizar_imagenes(imagenes)


class ProductoResumen(ResponseSchema):
    id: int = Field(gt=0)
    nombre: str
    slug: str
    precio: Decimal
    disponible: bool
    estado: Estado
    imagen_principal: ImagenResponse | None = None
    categoria: CategoriaResumen

    @field_serializer("precio")
    def _serializar_precio(self, valor: Decimal) -> float:
        return serializar_precio(valor)


class ProductoResponse(TimestampsResponse):
    id: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=150)
    slug: str
    descripcion: str | None = Field(default=None, max_length=5000)
    precio: Decimal
    sku: str = Field(min_length=3, max_length=50)
    categoria: CategoriaResumen
    colecciones: list[ColeccionResumen]
    existencias: Existencias
    disponible: bool
    imagenes: list[ImagenResponse]
    estado: Estado

    @field_serializer("precio")
    def _serializar_precio(self, valor: Decimal) -> float:
        return serializar_precio(valor)


class ProductoFiltros(RequestSchema):
    categoria: SlugOpcional = None
    categoria_id: int | None = Field(default=None, gt=0)
    nombre: str | None = None
    disponible: bool | None = None
    coleccion: SlugOpcional = None
    coleccion_id: int | None = Field(default=None, gt=0)
    estado: EstadoFiltro = EstadoFiltro.ACTIVO
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=20, ge=1, le=100)
    orden: OrdenProducto = OrdenProducto.RECIENTE

    def validar_combinaciones(self) -> None:
        if self.categoria is not None and self.categoria_id is not None:
            raise ValueError(
                "No se pueden enviar 'categoria' y 'categoria_id' al mismo tiempo."
            )
        if self.coleccion is not None and self.coleccion_id is not None:
            raise ValueError(
                "No se pueden enviar 'coleccion' y 'coleccion_id' al mismo tiempo."
            )


ProductoListaResponse = RespuestaLista[ProductoResumen]
