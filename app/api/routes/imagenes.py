from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Response,
    UploadFile,
    status,
)

from app.api.deps import get_imagen_service, requiere_administrador
from app.core.config import settings
from app.schemas.imagen import ImagenProductoResponse, ImagenUpdate
from app.services.imagenes import ImagenProductoService

router = APIRouter(prefix="/productos", tags=["imagenes"])


@router.post(
    "/{producto_id}/imagenes",
    response_model=ImagenProductoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_administrador)],
    summary="Subir una imagen de producto",
)
async def subir_imagen(
    producto_id: Annotated[int, Path(gt=0)],
    archivo: Annotated[UploadFile, File()],
    service: Annotated[ImagenProductoService, Depends(get_imagen_service)],
    texto_alternativo: Annotated[
        str | None, Form(max_length=150)
    ] = None,
    orden: Annotated[int | None, Form(ge=0)] = None,
    es_principal: Annotated[bool, Form()] = False,
) -> ImagenProductoResponse:
    contenido = await archivo.read(
        settings.max_image_size_bytes + 1
    )
    return service.subir(
        producto_id=producto_id,
        contenido=contenido,
        texto_alternativo=texto_alternativo,
        orden=orden,
        es_principal=es_principal,
    )


@router.put(
    "/{producto_id}/imagenes/{imagen_id}",
    response_model=ImagenProductoResponse,
    dependencies=[Depends(requiere_administrador)],
    summary="Actualizar metadatos de una imagen",
)
def actualizar_imagen(
    producto_id: Annotated[int, Path(gt=0)],
    imagen_id: Annotated[int, Path(gt=0)],
    datos: ImagenUpdate,
    service: Annotated[ImagenProductoService, Depends(get_imagen_service)],
) -> ImagenProductoResponse:
    return service.actualizar(
        producto_id,
        imagen_id,
        texto_alternativo=datos.texto_alternativo,
        orden=datos.orden,
        es_principal=datos.es_principal,
    )


@router.delete(
    "/{producto_id}/imagenes/{imagen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(requiere_administrador)],
    summary="Eliminar una imagen de producto",
)
def eliminar_imagen(
    producto_id: Annotated[int, Path(gt=0)],
    imagen_id: Annotated[int, Path(gt=0)],
    service: Annotated[ImagenProductoService, Depends(get_imagen_service)],
) -> Response:
    service.eliminar(producto_id, imagen_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
