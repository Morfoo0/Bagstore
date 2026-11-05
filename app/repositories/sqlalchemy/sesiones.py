from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sesion import Sesion
from app.repositories.sesiones import SesionAlmacenada
from app.repositories.sqlalchemy.mapeadores import sesion_a_entidad


class SesionRepositorioSQLAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def crear(
        self,
        *,
        usuario_id: int,
        token_hash: str,
        creado_en: datetime,
        expira_en: datetime,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> SesionAlmacenada:
        sesion = Sesion(
            usuario_id=usuario_id,
            token_hash=token_hash,
            creado_en=creado_en,
            expira_en=expira_en,
            user_agent=user_agent,
            ip=ip,
        )
        self._session.add(sesion)
        self._session.flush()
        return sesion_a_entidad(sesion)

    def obtener_por_token_hash(
        self, token_hash: str
    ) -> SesionAlmacenada | None:
        sesion = self._session.scalars(
            select(Sesion).where(Sesion.token_hash == token_hash)
        ).first()
        return sesion_a_entidad(sesion) if sesion is not None else None

    def revocar(self, sesion_id: int, revocado_en: datetime) -> None:
        sesion = self._session.get(Sesion, sesion_id)
        if sesion is None:
            return
        sesion.revocado_en = revocado_en
        self._session.flush()
