from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.sqlalchemy.mapeadores import usuario_a_entidad
from app.repositories.usuarios import UsuarioAlmacenado, UsuarioNuevo


class UsuarioRepositorioSQLAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_email(self, email: str) -> UsuarioAlmacenado | None:
        usuario = self._session.scalars(
            select(Usuario).where(Usuario.email == email.strip().lower())
        ).first()
        return usuario_a_entidad(usuario) if usuario is not None else None

    def obtener_por_id(self, usuario_id: int) -> UsuarioAlmacenado | None:
        usuario = self._session.get(Usuario, usuario_id)
        return usuario_a_entidad(usuario) if usuario is not None else None

    def crear(self, datos: UsuarioNuevo) -> UsuarioAlmacenado:
        usuario = Usuario(
            nombre=datos.nombre,
            email=datos.email,
            telefono=datos.telefono,
            password_hash=datos.password_hash,
            rol=datos.rol,
            estado=datos.estado,
        )
        self._session.add(usuario)
        self._session.flush()
        self._session.refresh(usuario)
        return usuario_a_entidad(usuario)

    def existe_email(self, email: str) -> bool:
        return bool(
            self._session.scalar(
                select(
                    func.count(Usuario.id)
                ).where(Usuario.email == email.strip().lower())
            )
        )
