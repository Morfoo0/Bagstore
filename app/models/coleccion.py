from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.producto_coleccion import producto_coleccion
from app.schemas.common import Estado


class Coleccion(Base):
    __tablename__ = "colecciones"
    __table_args__ = (
        Index("ix_colecciones_estado", "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_busqueda: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(150), nullable=False, unique=True, index=True
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[Estado] = mapped_column(
        Enum(
            Estado,
            name="estado_coleccion",
            values_callable=lambda enum: [valor.value for valor in enum],
        ),
        nullable=False,
        default=Estado.ACTIVO,
    )
    imagen_portada_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
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

    productos = relationship(
        "Producto",
        secondary=producto_coleccion,
        back_populates="colecciones",
    )


Index(
    "ux_colecciones_nombre_lower",
    func.lower(Coleccion.nombre),
    unique=True,
)
