from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.text import normalizar_texto
from app.models.categoria import Categoria
from app.repositories.categorias import (
    CategoriaAlmacenada,
    CategoriaConsulta,
    CategoriaNueva,
    CategoriaReemplazo,
)
from app.repositories.sqlalchemy.mapeadores import categoria_a_entidad
from app.schemas.common import Estado, EstadoFiltro


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class CategoriaRepositorioSQLAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def listar(
        self, consulta: CategoriaConsulta | None = None
    ) -> list[CategoriaAlmacenada]:
        stmt = select(Categoria)

        if consulta is not None:
            if consulta.estado == EstadoFiltro.ACTIVO:
                stmt = stmt.where(Categoria.estado == Estado.ACTIVO)
            elif consulta.estado == EstadoFiltro.INACTIVO:
                stmt = stmt.where(Categoria.estado == Estado.INACTIVO)

            if consulta.nombre:
                termino = normalizar_texto(consulta.nombre)
                if termino:
                    stmt = stmt.where(
                        Categoria.nombre_busqueda.ilike(f"%{termino}%")
                    )

        stmt = stmt.order_by(Categoria.orden.asc(), Categoria.id.asc())
        categorias = self._session.scalars(stmt).all()
        return [categoria_a_entidad(categoria) for categoria in categorias]

    def obtener_por_id(self, categoria_id: int) -> CategoriaAlmacenada | None:
        categoria = self._session.get(Categoria, categoria_id)
        return (
            categoria_a_entidad(categoria)
            if categoria is not None
            else None
        )

    def obtener_por_slug(self, slug: str) -> CategoriaAlmacenada | None:
        categoria = self._session.scalars(
            select(Categoria).where(
                Categoria.slug == slug.strip().lower()
            )
        ).first()
        return (
            categoria_a_entidad(categoria)
            if categoria is not None
            else None
        )

    def crear(self, datos: CategoriaNueva) -> CategoriaAlmacenada:
        ahora = _ahora()
        categoria = Categoria(
            nombre=datos.nombre,
            nombre_busqueda=normalizar_texto(datos.nombre),
            slug=datos.slug,
            descripcion=datos.descripcion,
            estado=datos.estado,
            orden=datos.orden,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        self._session.add(categoria)
        self._session.flush()
        return categoria_a_entidad(categoria)

    def reemplazar(
        self, categoria_id: int, datos: CategoriaReemplazo
    ) -> CategoriaAlmacenada:
        categoria = self._session.get(Categoria, categoria_id)
        if categoria is None:
            raise KeyError(categoria_id)
        categoria.nombre = datos.nombre
        categoria.nombre_busqueda = normalizar_texto(datos.nombre)
        categoria.slug = datos.slug
        categoria.descripcion = datos.descripcion
        categoria.estado = datos.estado
        categoria.orden = datos.orden
        categoria.actualizado_en = _ahora()
        self._session.flush()
        return categoria_a_entidad(categoria)

    def eliminar(self, categoria_id: int) -> bool:
        categoria = self._session.get(Categoria, categoria_id)
        if categoria is None:
            return False
        self._session.delete(categoria)
        self._session.flush()
        return True

    def existe_nombre(
        self, nombre: str, excluir_id: int | None = None
    ) -> bool:
        stmt = select(Categoria).where(
            Categoria.nombre_busqueda == normalizar_texto(nombre)
        )
        if excluir_id is not None:
            stmt = stmt.where(Categoria.id != excluir_id)
        return self._session.scalars(stmt).first() is not None

    def existe_slug(self, slug: str, excluir_id: int | None = None) -> bool:
        stmt = select(Categoria).where(
            Categoria.slug == slug.strip().lower()
        )
        if excluir_id is not None:
            stmt = stmt.where(Categoria.id != excluir_id)
        return self._session.scalars(stmt).first() is not None
