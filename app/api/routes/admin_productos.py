from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.deps import get_producto_service, requiere_administrador
from app.schemas.producto import ProductoEstadoUpdate, ProductoResponse
from app.services.productos import ProductoService

router = APIRouter(
    prefix="/admin/productos",
    tags=["admin-productos"],
    dependencies=[Depends(requiere_administrador)],
)


@router.put(
    "/{producto_id}/estado",
    response_model=ProductoResponse,
    summary="Activar o desactivar un producto",
)
def cambiar_estado_producto(
    producto_id: Annotated[int, Path(gt=0)],
    datos: ProductoEstadoUpdate,
    service: Annotated[ProductoService, Depends(get_producto_service)],
) -> ProductoResponse:
    return service.cambiar_estado(producto_id, datos.estado)
