from fastapi import APIRouter

from app.api.routes import health, productos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(productos.router)
