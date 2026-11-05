from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import (
    get_categoria_service,
    get_es_administrador,
    requiere_administrador,
)
from app.core.config import settings
from app.schemas.categoria import (
    CategoriaCreate,
    CategoriaFiltros,
    CategoriaListaResponse,
    CategoriaResponse,
    CategoriaUpdate,
)
from app.services.categorias import CategoriaService

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get(
    "",
    response_model=CategoriaListaResponse,
    summary="Listar categorías",
)
def listar_categorias(
    filtros: Annotated[CategoriaFiltros, Query()],
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
    es_administrador: Annotated[bool, Depends(get_es_administrador)],
) -> CategoriaListaResponse:
    return service.listar(
        filtros, es_administrador=es_administrador
    )


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Obtener una categoría",
)
def obtener_categoria(
    categoria_id: Annotated[int, Path(gt=0)],
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
    es_administrador: Annotated[bool, Depends(get_es_administrador)],
) -> CategoriaResponse:
    return service.obtener(
        categoria_id, es_administrador=es_administrador
    )


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_administrador)],
    summary="Crear una categoría",
)
def crear_categoria(
    datos: CategoriaCreate,
    response: Response,
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
) -> CategoriaResponse:
    categoria = service.crear(datos)
    response.headers["Location"] = (
        f"{settings.api_prefix}/categorias/{categoria.id}"
    )
    return categoria


@router.put(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    dependencies=[Depends(requiere_administrador)],
    summary="Reemplazar una categoría",
)
def actualizar_categoria(
    categoria_id: Annotated[int, Path(gt=0)],
    datos: CategoriaUpdate,
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
) -> CategoriaResponse:
    return service.actualizar(categoria_id, datos)


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(requiere_administrador)],
    summary="Eliminar una categoría",
)
def eliminar_categoria(
    categoria_id: Annotated[int, Path(gt=0)],
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
) -> Response:
    service.eliminar(categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
