from fastapi import APIRouter

from app.api.routes import (
    admin_colecciones,
    admin_productos,
    auth,
    categorias,
    colecciones,
    colores,
    health,
    imagenes,
    productos,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(productos.router)
api_router.include_router(imagenes.router)
api_router.include_router(colores.router)
api_router.include_router(categorias.router)
api_router.include_router(colecciones.router)
api_router.include_router(admin_colecciones.router)
api_router.include_router(admin_productos.router)
