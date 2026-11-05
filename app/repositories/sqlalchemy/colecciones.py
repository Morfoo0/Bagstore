from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.text import normalizar_texto
from app.models.coleccion import Coleccion
from app.models.producto import Producto
from app.models.producto_coleccion import producto_coleccion
from app.repositories.colecciones import (
    ColeccionAlmacenada,
    ColeccionConsulta,
    ColeccionNueva,
    ColeccionReemplazo,
)
from app.repositories.sqlalchemy.mapeadores import coleccion_a_entidad
from app.schemas.common import Estado, EstadoFiltro


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class ColeccionRepositorioSQLAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def listar(
        self, consulta: ColeccionConsulta | None = None
    ) -> list[ColeccionAlmacenada]:
        stmt = select(Coleccion).options(selectinload(Coleccion.productos))

        if consulta is not None:
            if consulta.estado == EstadoFiltro.ACTIVO:
                stmt = stmt.where(Coleccion.estado == Estado.ACTIVO)
            elif consulta.estado == EstadoFiltro.INACTIVO:
                stmt = stmt.where(Coleccion.estado == Estado.INACTIVO)

            if consulta.nombre:
                termino = normalizar_texto(consulta.nombre)
                if termino:
                    stmt = stmt.where(
                        Coleccion.nombre_busqueda.ilike(f"%{termino}%")
                    )

        stmt = stmt.order_by(Coleccion.id.asc())
        colecciones = self._session.scalars(stmt).all()
        return [
            coleccion_a_entidad(coleccion) for coleccion in colecciones
        ]

    def obtener_por_id(
        self, coleccion_id: int
    ) -> ColeccionAlmacenada | None:
        stmt = (
            select(Coleccion)
            .where(Coleccion.id == coleccion_id)
            .options(selectinload(Coleccion.productos))
        )
        coleccion = self._session.scalars(stmt).first()
        return (
            coleccion_a_entidad(coleccion)
            if coleccion is not None
            else None
        )

    def obtener_por_slug(self, slug: str) -> ColeccionAlmacenada | None:
        stmt = (
            select(Coleccion)
            .where(Coleccion.slug == slug.strip().lower())
            .options(selectinload(Coleccion.productos))
        )
        coleccion = self._session.scalars(stmt).first()
        return (
            coleccion_a_entidad(coleccion)
            if coleccion is not None
            else None
        )

    def crear(self, datos: ColeccionNueva) -> ColeccionAlmacenada:
        ahora = _ahora()
        coleccion = Coleccion(
            nombre=datos.nombre,
            nombre_busqueda=normalizar_texto(datos.nombre),
            slug=datos.slug,
            descripcion=datos.descripcion,
            estado=datos.estado,
            imagen_portada_url=datos.imagen_portada_url,
            creado_en=ahora,
            actualizado_en=ahora,
            productos=self._productos_por_ids(datos.producto_ids),
        )
        self._session.add(coleccion)
        self._session.flush()
        return coleccion_a_entidad(coleccion)

    def reemplazar(
        self, coleccion_id: int, datos: ColeccionReemplazo
    ) -> ColeccionAlmacenada:
        stmt = (
            select(Coleccion)
            .where(Coleccion.id == coleccion_id)
            .options(selectinload(Coleccion.productos))
        )
        coleccion = self._session.scalars(stmt).first()
        if coleccion is None:
            raise KeyError(coleccion_id)

        coleccion.nombre = datos.nombre
        coleccion.nombre_busqueda = normalizar_texto(datos.nombre)
        coleccion.slug = datos.slug
        coleccion.descripcion = datos.descripcion
        coleccion.estado = datos.estado
        coleccion.imagen_portada_url = datos.imagen_portada_url
        coleccion.actualizado_en = _ahora()
        coleccion.productos = self._productos_por_ids(datos.producto_ids)
        self._session.flush()
        return coleccion_a_entidad(coleccion)

    def eliminar(self, coleccion_id: int) -> bool:
        coleccion = self._session.get(Coleccion, coleccion_id)
        if coleccion is None:
            return False
        self._session.delete(coleccion)
        self._session.flush()
        return True

    def existe_nombre(
        self, nombre: str, excluir_id: int | None = None
    ) -> bool:
        stmt = select(Coleccion).where(
            Coleccion.nombre_busqueda == normalizar_texto(nombre)
        )
        if excluir_id is not None:
            stmt = stmt.where(Coleccion.id != excluir_id)
        return self._session.scalars(stmt).first() is not None

    def existe_slug(self, slug: str, excluir_id: int | None = None) -> bool:
        stmt = select(Coleccion).where(
            Coleccion.slug == slug.strip().lower()
        )
        if excluir_id is not None:
            stmt = stmt.where(Coleccion.id != excluir_id)
        return self._session.scalars(stmt).first() is not None

    def listar_por_producto(
        self, producto_id: int
    ) -> list[ColeccionAlmacenada]:
        stmt = (
            select(Coleccion)
            .join(
                producto_coleccion,
                producto_coleccion.c.coleccion_id == Coleccion.id,
            )
            .where(producto_coleccion.c.producto_id == producto_id)
            .options(selectinload(Coleccion.productos))
            .order_by(Coleccion.id.asc())
        )
        colecciones = self._session.scalars(stmt).all()
        return [
            coleccion_a_entidad(coleccion) for coleccion in colecciones
        ]

    def eliminar_producto_de_todas(self, producto_id: int) -> None:
        coleccion_ids = list(
            self._session.scalars(
                select(producto_coleccion.c.coleccion_id).where(
                    producto_coleccion.c.producto_id == producto_id
                )
            ).all()
        )
        if not coleccion_ids:
            return
        self._session.execute(
            delete(producto_coleccion).where(
                producto_coleccion.c.producto_id == producto_id
            )
        )
        self._session.execute(
            update(Coleccion)
            .where(Coleccion.id.in_(coleccion_ids))
            .values(actualizado_en=_ahora())
        )
        self._session.flush()

    def _productos_por_ids(self, producto_ids) -> list[Producto]:
        ids = set(producto_ids)
        if not ids:
            return []
        return list(
            self._session.scalars(
                select(Producto).where(Producto.id.in_(ids))
            ).all()
        )
