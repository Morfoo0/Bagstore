from functools import lru_cache

from fastapi import Depends

from app.repositories.categorias import CategoriaRepositorioMemoria
from app.repositories.colecciones import ColeccionRepositorioMemoria
from app.repositories.productos import ProductoRepositorioMemoria
from app.services.categorias import CategoriaService
from app.services.colecciones import ColeccionService
from app.services.productos import ProductoService


@lru_cache
def get_producto_repositorio() -> ProductoRepositorioMemoria:
    return ProductoRepositorioMemoria()


@lru_cache
def get_categoria_repositorio() -> CategoriaRepositorioMemoria:
    return CategoriaRepositorioMemoria()


@lru_cache
def get_coleccion_repositorio() -> ColeccionRepositorioMemoria:
    return ColeccionRepositorioMemoria()


def get_producto_service(
    productos: ProductoRepositorioMemoria = Depends(get_producto_repositorio),
    categorias: CategoriaRepositorioMemoria = Depends(get_categoria_repositorio),
    colecciones: ColeccionRepositorioMemoria = Depends(
        get_coleccion_repositorio
    ),
) -> ProductoService:
    return ProductoService(productos, categorias, colecciones)


def get_categoria_service(
    categorias: CategoriaRepositorioMemoria = Depends(
        get_categoria_repositorio
    ),
    productos: ProductoRepositorioMemoria = Depends(get_producto_repositorio),
) -> CategoriaService:
    return CategoriaService(categorias, productos)


def get_coleccion_service(
    colecciones: ColeccionRepositorioMemoria = Depends(
        get_coleccion_repositorio
    ),
    productos: ProductoRepositorioMemoria = Depends(get_producto_repositorio),
) -> ColeccionService:
    return ColeccionService(colecciones, productos)


def requiere_administrador() -> None:
    return None
