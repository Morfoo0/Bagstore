from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.text import normalizar_texto
from app.models.color import Color
from app.models.producto import Producto
from app.models.producto_color import producto_color
from app.repositories.colores import (
    ColorAlmacenado,
    ColorConsulta,
    ColorNuevo,
    ColorReemplazo,
)


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _a_entidad(color: Color) -> ColorAlmacenado:
    return ColorAlmacenado(
        id=color.id,
        nombre=color.nombre,
        nombre_normalizado=color.nombre_normalizado,
        tono=color.tono,
        producto_ids=tuple(
            sorted(producto.id for producto in color.productos)
        ),
        creado_en=color.creado_en,
        actualizado_en=color.actualizado_en,
    )


class ColorRepositorioSQLAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def listar(
        self, consulta: ColorConsulta | None = None
    ) -> list[ColorAlmacenado]:
        stmt = select(Color).options(selectinload(Color.productos))
        if consulta is not None and consulta.nombre:
            termino = normalizar_texto(consulta.nombre)
            if termino:
                stmt = stmt.where(
                    Color.nombre_normalizado.ilike(f"%{termino}%")
                )
        stmt = stmt.order_by(Color.nombre_normalizado.asc(), Color.id.asc())
        colores = self._session.scalars(stmt).all()
        return [_a_entidad(color) for color in colores]

    def obtener_por_id(self, color_id: int) -> ColorAlmacenado | None:
        stmt = (
            select(Color)
            .where(Color.id == color_id)
            .options(selectinload(Color.productos))
        )
        color = self._session.scalars(stmt).first()
        return _a_entidad(color) if color is not None else None

    def crear(self, datos: ColorNuevo) -> ColorAlmacenado:
        ahora = _ahora()
        color = Color(
            nombre=datos.nombre,
            nombre_normalizado=datos.nombre_normalizado,
            tono=datos.tono,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        self._session.add(color)
        self._session.flush()
        return _a_entidad(color)

    def reemplazar(
        self, color_id: int, datos: ColorReemplazo
    ) -> ColorAlmacenado:
        color = self._session.get(Color, color_id)
        if color is None:
            raise KeyError(color_id)
        color.nombre = datos.nombre
        color.nombre_normalizado = datos.nombre_normalizado
        color.tono = datos.tono
        color.actualizado_en = _ahora()
        self._session.flush()
        return _a_entidad(color)

    def eliminar(self, color_id: int) -> bool:
        color = self._session.get(Color, color_id)
        if color is None:
            return False
        self._session.delete(color)
        self._session.flush()
        return True

    def existe_nombre(
        self, nombre: str, excluir_id: int | None = None
    ) -> bool:
        stmt = select(Color).where(
            Color.nombre_normalizado == normalizar_texto(nombre)
        )
        if excluir_id is not None:
            stmt = stmt.where(Color.id != excluir_id)
        return self._session.scalars(stmt).first() is not None

    def esta_asociado(self, color_id: int) -> bool:
        return bool(
            self._session.scalar(
                select(func.count())
                .select_from(producto_color)
                .where(producto_color.c.color_id == color_id)
            )
        )

    def listar_por_producto(
        self, producto_id: int
    ) -> list[ColorAlmacenado]:
        stmt = (
            select(Color)
            .join(
                producto_color,
                producto_color.c.color_id == Color.id,
            )
            .where(producto_color.c.producto_id == producto_id)
            .options(selectinload(Color.productos))
            .order_by(Color.nombre_normalizado.asc(), Color.id.asc())
        )
        colores = self._session.scalars(stmt).all()
        return [_a_entidad(color) for color in colores]

    def reemplazar_productos(
        self, producto_id: int, color_ids: list[int]
    ) -> None:
        producto = self._session.get(Producto, producto_id)
        if producto is None:
            raise KeyError(producto_id)
        colores = list(
            self._session.scalars(
                select(Color).where(Color.id.in_(set(color_ids)))
            ).all()
        )
        producto.colores = colores
        self._session.flush()
