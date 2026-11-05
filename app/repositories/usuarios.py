from dataclasses import dataclass
from datetime import datetime

from app.core.enums import RolUsuario
from app.schemas.common import Estado


@dataclass(frozen=True, slots=True)
class UsuarioAlmacenado:
    id: int
    nombre: str
    email: str
    telefono: str | None
    password_hash: str
    rol: RolUsuario
    estado: Estado
    creado_en: datetime
    actualizado_en: datetime


@dataclass(frozen=True, slots=True)
class UsuarioNuevo:
    nombre: str
    email: str
    telefono: str | None
    password_hash: str
    rol: RolUsuario
    estado: Estado
