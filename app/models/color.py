from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.producto_color import producto_color


class Color(Base):
    __tablename__ = "colores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    tono: Mapped[str] = mapped_column(String(7), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    productos = relationship(
        "Producto",
        secondary=producto_color,
        back_populates="colores",
    )
