from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import get_producto_service, requiere_administrador
from app.core.config import settings
from app.schemas.producto import (
    ProductoCreate,
    ProductoFiltros,
    ProductoListaResponse,
    ProductoResponse,
    ProductoUpdate,
)
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
) -> ProductoListaResponse:
    return service.listar(filtros)


@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Obtener un producto",
)
def obtener_producto(
    producto_id: Annotated[int, Path(gt=0)],
    service: Annotated[ProductoService, Depends(get_producto_service)],
) -> ProductoResponse:
    return service.obtener(producto_id)


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
