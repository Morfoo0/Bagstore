from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import RolUsuario
from app.schemas.common import Estado


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(
            RolUsuario,
            name="rol_usuario",
            values_callable=lambda enum: [valor.value for valor in enum],
        ),
        nullable=False,
        default=RolUsuario.CLIENTE,
    )
    estado: Mapped[Estado] = mapped_column(
        Enum(
            Estado,
            name="estado_usuario",
            values_callable=lambda enum: [valor.value for valor in enum],
        ),
        nullable=False,
        default=Estado.ACTIVO,
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    sesiones = relationship(
        "Sesion",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
