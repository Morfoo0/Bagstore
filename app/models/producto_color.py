from sqlalchemy import Column, ForeignKey, Index, Table

from app.core.database import Base

producto_color = Table(
    "producto_colores",
    Base.metadata,
    Column(
        "producto_id",
        ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "color_id",
        ForeignKey("colores.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)

Index("ix_producto_colores_color_id", producto_color.c.color_id)
