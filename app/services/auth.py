from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.enums import RolUsuario
from app.core.errors import AppError
from app.core.security import (
    ahora_utc,
    asegurar_utc,
    generar_token_sesion,
    hash_password,
    hash_token,
    normalizar_email,
    verificar_password,
)
from app.repositories.sesiones import SesionAlmacenada
from app.repositories.sqlalchemy.sesiones import SesionRepositorioSQLAlchemy
from app.repositories.sqlalchemy.usuarios import UsuarioRepositorioSQLAlchemy
from app.repositories.usuarios import UsuarioAlmacenado, UsuarioNuevo
from app.schemas.auth import (
    SesionResponse,
    TokenResponse,
    UsuarioLogin,
    UsuarioPublico,
    UsuarioRegistro,
)
from app.schemas.common import Estado
from app.schemas.errors import CodigoError, ErrorDetalle


@dataclass(frozen=True, slots=True)
class SesionActual:
    sesion: SesionAlmacenada
    usuario: UsuarioPublico


class AuthService:
    def __init__(
        self,
        usuarios: UsuarioRepositorioSQLAlchemy,
        sesiones: SesionRepositorioSQLAlchemy,
        session_ttl_minutes: int,
    ) -> None:
        self._usuarios = usuarios
        self._sesiones = sesiones
        self._session_ttl_minutes = session_ttl_minutes

    def registrar(self, datos: UsuarioRegistro) -> UsuarioPublico:
        email = normalizar_email(str(datos.email))
        if self._usuarios.existe_email(email):
            raise AppError(
                409,
                CodigoError.CONFLICTO_UNICIDAD,
                "Ya existe un usuario con el correo indicado.",
                [
                    ErrorDetalle(
                        campo="email",
                        mensaje=f"El correo '{email}' ya está registrado.",
                    )
                ],
            )

        telefono = datos.telefono.strip() if datos.telefono else None
        usuario = self._usuarios.crear(
            UsuarioNuevo(
                nombre=datos.nombre.strip(),
                email=email,
                telefono=telefono,
                password_hash=hash_password(datos.password),
                rol=RolUsuario.CLIENTE,
                estado=Estado.ACTIVO,
            )
        )
        return self._a_publico(usuario)

    def login(
        self,
        datos: UsuarioLogin,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> TokenResponse:
        usuario = self._usuarios.obtener_por_email(
            normalizar_email(str(datos.email))
        )
        if usuario is None or not verificar_password(
            datos.password, usuario.password_hash
        ):
            raise AppError(
                401,
                CodigoError.NO_AUTENTICADO,
                "Credenciales inválidas.",
            )
        if usuario.estado != Estado.ACTIVO:
            raise AppError(
                403,
                CodigoError.ACCESO_DENEGADO,
                "La cuenta está inactiva.",
            )

        ahora = ahora_utc()
        expira_en = ahora + timedelta(minutes=self._session_ttl_minutes)
        token = generar_token_sesion()
        self._sesiones.crear(
            usuario_id=usuario.id,
            token_hash=hash_token(token),
            creado_en=ahora,
            expira_en=expira_en,
            user_agent=user_agent,
            ip=ip,
        )
        return TokenResponse(
            access_token=token,
            expira_en=self._session_ttl_minutes * 60,
            usuario=self._a_publico(usuario),
        )

    def autenticar(self, token: str) -> SesionActual:
        sesion = self._sesiones.obtener_por_token_hash(hash_token(token))
        if sesion is None or sesion.revocado_en is not None:
            raise self._error_sesion()
        if asegurar_utc(sesion.expira_en) <= ahora_utc():
            raise self._error_sesion()

        usuario = self._usuarios.obtener_por_id(sesion.usuario_id)
        if usuario is None:
            raise self._error_sesion()
        if usuario.estado != Estado.ACTIVO:
            raise AppError(
                403,
                CodigoError.ACCESO_DENEGADO,
                "La cuenta está inactiva.",
            )
        return SesionActual(sesion=sesion, usuario=self._a_publico(usuario))

    def logout(self, token: str) -> None:
        sesion = self._sesiones.obtener_por_token_hash(hash_token(token))
        if sesion is None or sesion.revocado_en is not None:
            return
        self._sesiones.revocar(sesion.id, ahora_utc())

    def sesion(self, token: str) -> SesionResponse:
        actual = self.autenticar(token)
        return SesionResponse(
            usuario=actual.usuario,
            expira_en=actual.sesion.expira_en,
        )

    def _a_publico(self, usuario: UsuarioAlmacenado) -> UsuarioPublico:
        return UsuarioPublico(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            telefono=usuario.telefono,
            rol=usuario.rol,
            estado=usuario.estado,
            creado_en=usuario.creado_en,
        )

    def _error_sesion(self) -> AppError:
        return AppError(
            401,
            CodigoError.NO_AUTENTICADO,
            "Sesión inválida o expirada.",
        )
