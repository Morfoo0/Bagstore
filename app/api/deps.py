from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.enums import RolUsuario
from app.core.errors import AppError
from app.core.storage import AlmacenamientoLocal
from app.repositories.sqlalchemy.categorias import (
    CategoriaRepositorioSQLAlchemy,
)
from app.repositories.sqlalchemy.colores import ColorRepositorioSQLAlchemy
from app.repositories.sqlalchemy.colecciones import (
    ColeccionRepositorioSQLAlchemy,
)
from app.repositories.sqlalchemy.imagenes import (
    ImagenProductoRepositorioSQLAlchemy,
)
from app.repositories.sqlalchemy.productos import (
    ProductoRepositorioSQLAlchemy,
)
from app.repositories.sqlalchemy.sesiones import SesionRepositorioSQLAlchemy
from app.repositories.sqlalchemy.usuarios import UsuarioRepositorioSQLAlchemy
from app.schemas.auth import UsuarioPublico
from app.schemas.errors import CodigoError
from app.services.auth import AuthService, SesionActual
from app.services.categorias import CategoriaService
from app.services.colores import ColorService
from app.services.colecciones import ColeccionService
from app.services.imagenes import ImagenProductoService
from app.services.productos import ProductoService

_bearer = HTTPBearer(auto_error=False)


def get_producto_service(
    db: Annotated[Session, Depends(get_db)],
) -> ProductoService:
    return ProductoService(
        ProductoRepositorioSQLAlchemy(db),
        CategoriaRepositorioSQLAlchemy(db),
        ColeccionRepositorioSQLAlchemy(db),
        ColorRepositorioSQLAlchemy(db),
    )


def get_categoria_service(
    db: Annotated[Session, Depends(get_db)],
) -> CategoriaService:
    return CategoriaService(
        CategoriaRepositorioSQLAlchemy(db),
        ProductoRepositorioSQLAlchemy(db),
    )


def get_coleccion_service(
    db: Annotated[Session, Depends(get_db)],
) -> ColeccionService:
    return ColeccionService(
        ColeccionRepositorioSQLAlchemy(db),
        ProductoRepositorioSQLAlchemy(db),
    )


def get_color_service(
    db: Annotated[Session, Depends(get_db)],
) -> ColorService:
    return ColorService(
        ColorRepositorioSQLAlchemy(db),
        ProductoRepositorioSQLAlchemy(db),
    )


def get_almacenamiento() -> AlmacenamientoLocal:
    return AlmacenamientoLocal(
        settings.upload_dir,
        settings.media_base_url,
    )


def get_imagen_service(
    db: Annotated[Session, Depends(get_db)],
    almacenamiento: Annotated[
        AlmacenamientoLocal, Depends(get_almacenamiento)
    ],
) -> ImagenProductoService:
    return ImagenProductoService(
        ProductoRepositorioSQLAlchemy(db),
        ImagenProductoRepositorioSQLAlchemy(db),
        almacenamiento,
        settings.max_image_size_bytes,
    )


def get_auth_service(
    db: Annotated[Session, Depends(get_db)],
) -> AuthService:
    return AuthService(
        UsuarioRepositorioSQLAlchemy(db),
        SesionRepositorioSQLAlchemy(db),
        settings.session_ttl_minutes,
    )


def get_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            401,
            CodigoError.NO_AUTENTICADO,
            "Se requieren credenciales válidas para realizar esta operación.",
        )
    return credentials.credentials


def get_sesion_actual(
    token: Annotated[str, Depends(get_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> SesionActual:
    return service.autenticar(token)


def get_usuario_actual(
    actual: Annotated[SesionActual, Depends(get_sesion_actual)],
) -> UsuarioPublico:
    return actual.usuario


def get_usuario_opcional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UsuarioPublico | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise AppError(
            401,
            CodigoError.NO_AUTENTICADO,
            "Se requieren credenciales válidas para realizar esta operación.",
        )
    return service.autenticar(credentials.credentials).usuario


def get_es_administrador(
    usuario: Annotated[
        UsuarioPublico | None, Depends(get_usuario_opcional)
    ],
) -> bool:
    return (
        usuario is not None
        and usuario.rol == RolUsuario.ADMINISTRADOR
    )


def requiere_administrador(
    usuario: Annotated[UsuarioPublico, Depends(get_usuario_actual)],
) -> UsuarioPublico:
    if usuario.rol != RolUsuario.ADMINISTRADOR:
        raise AppError(
            403,
            CodigoError.ACCESO_DENEGADO,
            "Se requiere el rol administrador para realizar esta operación.",
        )
    return usuario
