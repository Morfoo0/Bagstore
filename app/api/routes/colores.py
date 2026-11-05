from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import get_color_service, requiere_administrador
from app.core.config import settings
from app.schemas.color import (
    ColorCreate,
    ColorFiltros,
    ColorListaResponse,
    ColorResponse,
    ColorUpdate,
)
from app.services.colores import ColorService

router = APIRouter(prefix="/colores", tags=["colores"])


@router.get(
    "",
    response_model=ColorListaResponse,
    summary="Listar colores",
)
def listar_colores(
    filtros: Annotated[ColorFiltros, Query()],
    service: Annotated[ColorService, Depends(get_color_service)],
) -> ColorListaResponse:
    return service.listar(filtros)


@router.get(
    "/{color_id}",
    response_model=ColorResponse,
    summary="Obtener un color",
)
def obtener_color(
    color_id: Annotated[int, Path(gt=0)],
    service: Annotated[ColorService, Depends(get_color_service)],
) -> ColorResponse:
    return service.obtener(color_id)


@router.post(
    "",
    response_model=ColorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_administrador)],
    summary="Crear un color",
)
def crear_color(
    datos: ColorCreate,
    response: Response,
    service: Annotated[ColorService, Depends(get_color_service)],
) -> ColorResponse:
    color = service.crear(datos)
    response.headers["Location"] = (
        f"{settings.api_prefix}/colores/{color.id}"
    )
    return color


@router.put(
    "/{color_id}",
    response_model=ColorResponse,
    dependencies=[Depends(requiere_administrador)],
    summary="Reemplazar un color",
)
def actualizar_color(
    color_id: Annotated[int, Path(gt=0)],
    datos: ColorUpdate,
    service: Annotated[ColorService, Depends(get_color_service)],
) -> ColorResponse:
    return service.actualizar(color_id, datos)


@router.delete(
    "/{color_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(requiere_administrador)],
    summary="Eliminar un color",
)
def eliminar_color(
    color_id: Annotated[int, Path(gt=0)],
    service: Annotated[ColorService, Depends(get_color_service)],
) -> Response:
    service.eliminar(color_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
