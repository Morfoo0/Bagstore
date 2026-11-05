from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.producto_coleccion import producto_coleccion
from app.schemas.common import Estado


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (
        Index("ix_productos_categoria_estado", "categoria_id", "estado"),
        Index("ix_productos_eliminado_en", "eliminado_en"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre_busqueda: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(150), nullable=False, unique=True, index=True
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    sku: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    existencias: Mapped[int] = mapped_column(nullable=False, default=0)
    estado: Mapped[Estado] = mapped_column(
        Enum(
            Estado,
            name="estado_producto",
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
    eliminado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    categoria = relationship("Categoria", back_populates="productos")
    imagenes = relationship(
        "ImagenProducto",
        back_populates="producto",
        cascade="all, delete-orphan",
        order_by="ImagenProducto.orden",
    )
    colecciones = relationship(
        "Coleccion",
        secondary=producto_coleccion,
        back_populates="productos",
    )
