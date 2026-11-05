from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import (
    get_coleccion_service,
    get_es_administrador,
    requiere_administrador,
)
from app.core.config import settings
from app.schemas.coleccion import (
    ColeccionCreate,
    ColeccionFiltros,
    ColeccionListaResponse,
    ColeccionResponse,
    ColeccionUpdate,
)
from app.services.colecciones import ColeccionService

router = APIRouter(prefix="/colecciones", tags=["colecciones"])


@router.get(
    "",
    response_model=ColeccionListaResponse,
    summary="Listar colecciones",
)
def listar_colecciones(
    filtros: Annotated[ColeccionFiltros, Query()],
    service: Annotated[ColeccionService, Depends(get_coleccion_service)],
    es_administrador: Annotated[bool, Depends(get_es_administrador)],
) -> ColeccionListaResponse:
    return service.listar(
        filtros, es_administrador=es_administrador
    )


@router.get(
    "/{coleccion_id}",
    response_model=ColeccionResponse,
    summary="Obtener una colección",
)
def obtener_coleccion(
    coleccion_id: Annotated[int, Path(gt=0)],
    service: Annotated[ColeccionService, Depends(get_coleccion_service)],
    es_administrador: Annotated[bool, Depends(get_es_administrador)],
) -> ColeccionResponse:
    return service.obtener(
        coleccion_id, es_administrador=es_administrador
    )


@router.post(
    "",
    response_model=ColeccionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_administrador)],
    summary="Crear una colección",
)
def crear_coleccion(
    datos: ColeccionCreate,
    response: Response,
    service: Annotated[ColeccionService, Depends(get_coleccion_service)],
) -> ColeccionResponse:
    coleccion = service.crear(datos)
    response.headers["Location"] = (
        f"{settings.api_prefix}/colecciones/{coleccion.id}"
    )
    return coleccion


@router.put(
    "/{coleccion_id}",
    response_model=ColeccionResponse,
    dependencies=[Depends(requiere_administrador)],
    summary="Reemplazar una colección",
)
def actualizar_coleccion(
    coleccion_id: Annotated[int, Path(gt=0)],
    datos: ColeccionUpdate,
    service: Annotated[ColeccionService, Depends(get_coleccion_service)],
) -> ColeccionResponse:
    return service.actualizar(coleccion_id, datos)


@router.delete(
    "/{coleccion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(requiere_administrador)],
    summary="Eliminar una colección",
)
def eliminar_coleccion(
    coleccion_id: Annotated[int, Path(gt=0)],
    service: Annotated[ColeccionService, Depends(get_coleccion_service)],
) -> Response:
    service.eliminar(coleccion_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
