from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SesionAlmacenada:
    id: int
    usuario_id: int
    token_hash: str
    creado_en: datetime
    expira_en: datetime
    revocado_en: datetime | None
    user_agent: str | None
    ip: str | None
