from pydantic import Field

from app.schemas.common import (
    MAX_IMAGENES,
    RequestSchema,
    ResponseSchema,
    TimestampsResponse,
    UrlHttp,
)


class ImagenCreate(RequestSchema):
    url: UrlHttp
    texto_alternativo: str | None = Field(default=None, max_length=150)
    orden: int | None = Field(default=None, ge=0)
    es_principal: bool = False


class ImagenUpdate(RequestSchema):
    texto_alternativo: str | None = Field(default=None, max_length=150)
    orden: int = Field(ge=0)
    es_principal: bool


class ImagenResponse(ResponseSchema):
    url: str = Field(min_length=1, max_length=500)
    texto_alternativo: str | None = Field(default=None, max_length=150)
    orden: int = Field(ge=0)
    es_principal: bool


class ImagenProductoResponse(TimestampsResponse):
    id: int = Field(gt=0)
    producto_id: int = Field(gt=0)
    url: str = Field(min_length=1, max_length=500)
    texto_alternativo: str | None = Field(default=None, max_length=150)
    orden: int = Field(ge=0)
    es_principal: bool


def normalizar_imagenes(imagenes: list[ImagenCreate]) -> list[ImagenCreate]:
    if len(imagenes) > MAX_IMAGENES:
        raise ValueError(f"No se permiten más de {MAX_IMAGENES} imágenes.")

    for indice, imagen in enumerate(imagenes):
        if imagen.orden is None:
            imagen.orden = indice + 1

    ordenes: set[int] = set()
    for imagen in imagenes:
        if imagen.orden in ordenes:
            raise ValueError("El campo 'orden' no puede repetirse entre imágenes.")
        ordenes.add(imagen.orden)

    principales = [imagen for imagen in imagenes if imagen.es_principal]
    if len(principales) > 1:
        raise ValueError("Solo una imagen puede marcarse como principal.")

    if imagenes and not principales:
        imagenes[0].es_principal = True

    return imagenes
