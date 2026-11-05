from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import (
    get_auth_service,
    get_sesion_actual,
    get_token,
)
from app.schemas.auth import (
    SesionResponse,
    TokenResponse,
    UsuarioLogin,
    UsuarioPublico,
    UsuarioRegistro,
)
from app.services.auth import AuthService, SesionActual

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/registro",
    response_model=UsuarioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cliente",
)
def registrar(
    datos: UsuarioRegistro,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UsuarioPublico:
    return service.registrar(datos)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
def login(
    datos: UsuarioLogin,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return service.login(datos, user_agent=user_agent, ip=ip)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Cerrar sesión",
)
def logout(
    token: Annotated[str, Depends(get_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    service.logout(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/sesion",
    response_model=SesionResponse,
    summary="Consultar sesión activa",
)
def sesion(
    actual: Annotated[SesionActual, Depends(get_sesion_actual)],
) -> SesionResponse:
    return SesionResponse(
        usuario=actual.usuario,
        expira_en=actual.sesion.expira_en,
    )
