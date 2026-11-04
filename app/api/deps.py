from functools import lru_cache

from fastapi import Depends

from app.repositories.categorias import CategoriaRepositorioMemoria
from app.repositories.colecciones import ColeccionRepositorioMemoria
from app.repositories.productos import ProductoRepositorioMemoria
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


def requiere_administrador() -> None:
    return None
