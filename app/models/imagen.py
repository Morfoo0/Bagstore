from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ImagenProducto(Base):
    __tablename__ = "imagenes_producto"
    __table_args__ = (
        UniqueConstraint(
            "producto_id",
            "orden",
            name="uq_imagen_producto_orden",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    texto_alternativo: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )
    orden: Mapped[int] = mapped_column(nullable=False, default=0)
    es_principal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
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

    producto = relationship("Producto", back_populates="imagenes")
