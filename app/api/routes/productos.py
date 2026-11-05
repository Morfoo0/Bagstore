from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import (
    get_color_service,
    get_es_administrador,
    get_producto_service,
    requiere_administrador,
)
from app.core.config import settings
from app.schemas.color import (
    ColoresProductoResponse,
    ProductoColoresUpdate,
)
from app.schemas.producto import (
    ProductoCreate,
    ProductoFiltros,
    ProductoListaResponse,
    ProductoResponse,
    ProductoUpdate,
)
from app.services.colores import ColorService
from app.services.productos import ProductoService

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get(
    "",
    response_model=ProductoListaResponse,
    summary="Listar productos",
)
def listar_productos(
    filtros: Annotated[ProductoFiltros, Query()],
    service: Annotated[ProductoService, Depends(get_producto_service)],
    es_administrador: Annotated[bool, Depends(get_es_administrador)],
) -> ProductoListaResponse:
    return service.listar(
        filtros, es_administrador=es_administrador
    )


@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Obtener un producto",
)
def obtener_producto(
    producto_id: Annotated[int, Path(gt=0)],
    service: Annotated[ProductoService, Depends(get_producto_service)],
    es_administrador: Annotated[bool, Depends(get_es_administrador)],
) -> ProductoResponse:
    return service.obtener(
        producto_id, es_administrador=es_administrador
    )


@router.get(
    "/{producto_id}/colores",
    response_model=ColoresProductoResponse,
    summary="Obtener colores de un producto",
)
def obtener_colores_producto(
    producto_id: Annotated[int, Path(gt=0)],
    service: Annotated[ColorService, Depends(get_color_service)],
    es_administrador: Annotated[bool, Depends(get_es_administrador)],
) -> ColoresProductoResponse:
    return service.listar_por_producto(
        producto_id, es_administrador=es_administrador
    )


@router.put(
    "/{producto_id}/colores",
    response_model=ColoresProductoResponse,
    dependencies=[Depends(requiere_administrador)],
    summary="Reemplazar colores de un producto",
)
def reemplazar_colores_producto(
    producto_id: Annotated[int, Path(gt=0)],
    datos: ProductoColoresUpdate,
    service: Annotated[ColorService, Depends(get_color_service)],
) -> ColoresProductoResponse:
    return service.reemplazar_producto(producto_id, datos)


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_administrador)],
    summary="Crear un producto",
)
def crear_producto(
    datos: ProductoCreate,
    response: Response,
    service: Annotated[ProductoService, Depends(get_producto_service)],
) -> ProductoResponse:
    producto = service.crear(datos)
    response.headers["Location"] = (
        f"{settings.api_prefix}/productos/{producto.id}"
    )
    return producto


@router.put(
    "/{producto_id}",
    response_model=ProductoResponse,
    dependencies=[Depends(requiere_administrador)],
    summary="Reemplazar un producto",
)
def actualizar_producto(
    producto_id: Annotated[int, Path(gt=0)],
    datos: ProductoUpdate,
    service: Annotated[ProductoService, Depends(get_producto_service)],
) -> ProductoResponse:
    return service.actualizar(producto_id, datos)


@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(requiere_administrador)],
    summary="Eliminar un producto",
)
def eliminar_producto(
    producto_id: Annotated[int, Path(gt=0)],
    service: Annotated[ProductoService, Depends(get_producto_service)],
) -> Response:
    service.eliminar(producto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
