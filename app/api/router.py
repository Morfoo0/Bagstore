from fastapi import APIRouter

from app.api.routes import auth, categorias, colecciones, health, productos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(productos.router)
api_router.include_router(categorias.router)
api_router.include_router(colecciones.router)
