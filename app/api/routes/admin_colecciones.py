from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import (
    get_coleccion_service,
    get_producto_service,
    requiere_administrador,
)
from app.schemas.coleccion import (
    ColeccionAdminFiltros,
    ColeccionListaResponse,
    ColeccionResponse,
)
from app.schemas.producto import (
    ProductoListaResponse,
    ProductosDeColeccionFiltros,
)
from app.services.colecciones import ColeccionService
from app.services.productos import ProductoService

router = APIRouter(
    prefix="/admin/colecciones",
    tags=["admin-colecciones"],
    dependencies=[Depends(requiere_administrador)],
)


@router.get(
    "",
    response_model=ColeccionListaResponse,
    summary="Listar colecciones para administración",
)
def listar_colecciones_admin(
    filtros: Annotated[ColeccionAdminFiltros, Query()],
    service: Annotated[ColeccionService, Depends(get_coleccion_service)],
) -> ColeccionListaResponse:
    return service.listar(filtros, es_administrador=True)


@router.get(
    "/{coleccion_id}",
    response_model=ColeccionResponse,
    summary="Obtener una colección para administración",
)
def obtener_coleccion_admin(
    coleccion_id: Annotated[int, Path(gt=0)],
    service: Annotated[ColeccionService, Depends(get_coleccion_service)],
) -> ColeccionResponse:
    return service.obtener(coleccion_id, es_administrador=True)


@router.get(
    "/{coleccion_id}/productos",
    response_model=ProductoListaResponse,
    summary="Listar productos de una colección, activos e inactivos",
)
def listar_productos_coleccion_admin(
    coleccion_id: Annotated[int, Path(gt=0)],
    filtros: Annotated[ProductosDeColeccionFiltros, Query()],
    service: Annotated[ProductoService, Depends(get_producto_service)],
) -> ProductoListaResponse:
    return service.listar_por_coleccion(
        coleccion_id,
        filtros,
        es_administrador=True,
    )
