import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, Generic, TypeVar

from pydantic import (
    AfterValidator,
    AnyHttpUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_serializer,
)

T = TypeVar("T")

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKU_PATTERN = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")

MAX_PRECIO = Decimal("999999.99")
MAX_EXISTENCIAS = 1_000_000
MAX_IMAGENES = 10
MAX_PRODUCTOS_COLECCION = 200


class Estado(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"


class EstadoFiltro(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    TODOS = "todos"


class RequestSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class ResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Paginacion(ResponseSchema):
    pagina: int = Field(ge=1)
    por_pagina: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_paginas: int = Field(ge=0)


class RespuestaLista(ResponseSchema, Generic[T]):
    datos: list[T]
    paginacion: Paginacion


def normalizar_slug(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor.strip().lower())
    normalizado = "".join(
        caracter for caracter in normalizado if not unicodedata.combining(caracter)
    )
    normalizado = re.sub(r"[\s_]+", "-", normalizado)
    normalizado = re.sub(r"[^a-z0-9-]", "", normalizado)
    return re.sub(r"-{2,}", "-", normalizado).strip("-")


def normalizar_sku(valor: str) -> str:
    return valor.strip().upper()


def _validar_slug(valor: str | None) -> str | None:
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError("El slug debe ser texto.")
    slug = normalizar_slug(valor)
    if not slug:
        raise ValueError("El slug no puede estar vacío.")
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(
            "El slug solo admite minúsculas, números y guiones simples."
        )
    return slug


def _validar_url_http(valor: str | None) -> str | None:
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError("La URL debe ser texto.")
    url = valor.strip()
    if not url:
        raise ValueError("La URL no puede estar vacía.")
    if len(url) > 500:
        raise ValueError("La URL no puede superar los 500 caracteres.")
    try:
        AnyHttpUrl(url)
    except ValidationError as exc:
        raise ValueError("La URL debe ser válida y usar http o https.") from exc
    return url


def _validar_precio(valor: Decimal) -> Decimal:
    if not valor.is_finite():
        raise ValueError("El precio debe ser un número finito.")
    return valor


SlugOpcional = Annotated[str | None, BeforeValidator(_validar_slug)]
UrlHttp = Annotated[str, BeforeValidator(_validar_url_http)]
UrlHttpOpcional = Annotated[str | None, BeforeValidator(_validar_url_http)]
Precio = Annotated[
    Decimal,
    Field(gt=0, le=MAX_PRECIO, max_digits=8, decimal_places=2),
    AfterValidator(_validar_precio),
]
Existencias = Annotated[int, Field(ge=0, le=MAX_EXISTENCIAS)]


class TimestampsResponse(ResponseSchema):
    creado_en: datetime
    actualizado_en: datetime

    @field_serializer("creado_en", "actualizado_en")
    def _serializar_fecha_utc(self, valor: datetime) -> str:
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def serializar_precio(valor: Decimal) -> float:
    return float(valor)
