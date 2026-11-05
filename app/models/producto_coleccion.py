from sqlalchemy import Column, ForeignKey, Index, Table

from app.core.database import Base

producto_coleccion = Table(
    "producto_coleccion",
    Base.metadata,
    Column(
        "producto_id",
        ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "coleccion_id",
        ForeignKey("colecciones.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

Index(
    "ix_producto_coleccion_coleccion_id",
    producto_coleccion.c.coleccion_id,
)
