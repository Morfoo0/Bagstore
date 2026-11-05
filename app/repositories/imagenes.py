from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ImagenProductoAlmacenada:
    id: int
    producto_id: int
    url: str
    storage_key: str | None
    texto_alternativo: str | None
    orden: int
    es_principal: bool
    creado_en: datetime
    actualizado_en: datetime


@dataclass(frozen=True, slots=True)
class ImagenProductoNueva:
    producto_id: int
    url: str
    storage_key: str | None
    texto_alternativo: str | None
    orden: int
    es_principal: bool


@dataclass(frozen=True, slots=True)
class ImagenProductoActualizacion:
    texto_alternativo: str | None
    orden: int
    es_principal: bool
