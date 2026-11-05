from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ColorAlmacenado:
    id: int
    nombre: str
    nombre_normalizado: str
    tono: str
    producto_ids: tuple[int, ...]
    creado_en: datetime
    actualizado_en: datetime


@dataclass(frozen=True, slots=True)
class ColorNuevo:
    nombre: str
    nombre_normalizado: str
    tono: str


@dataclass(frozen=True, slots=True)
class ColorReemplazo:
    nombre: str
    nombre_normalizado: str
    tono: str


@dataclass(frozen=True, slots=True)
class ColorConsulta:
    nombre: str | None = None
