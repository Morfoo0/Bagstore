from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.core.enums import RolUsuario
from app.schemas.common import Estado, ResponseSchema


class AuthRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UsuarioRegistro(AuthRequestSchema):
    nombre: Annotated[str, Field(min_length=2, max_length=150)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    telefono: Annotated[str | None, Field(max_length=30)] = None


class UsuarioLogin(AuthRequestSchema):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]


class UsuarioPublico(ResponseSchema):
    id: int = Field(gt=0)
    nombre: str
    email: EmailStr
    telefono: str | None = None
    rol: RolUsuario
    estado: Estado
    creado_en: datetime

    @field_serializer("creado_en")
    def _serializar_creado_en(self, valor: datetime) -> str:
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: int
    usuario: UsuarioPublico


class SesionResponse(BaseModel):
    autenticado: bool = True
    usuario: UsuarioPublico
    expira_en: datetime

    @field_serializer("expira_en")
    def _serializar_expira_en(self, valor: datetime) -> str:
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
