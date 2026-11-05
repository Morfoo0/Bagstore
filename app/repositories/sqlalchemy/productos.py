from datetime import datetime, timezone

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.text import normalizar_texto
from app.models.imagen import ImagenProducto
from app.models.producto import Producto
from app.repositories.productos import (
    ProductoAlmacenado,
    ProductoConsulta,
    ProductoNuevo,
    ProductoReemplazo,
)
from app.repositories.sqlalchemy.mapeadores import producto_a_entidad
from app.schemas.common import Estado, EstadoFiltro
from app.schemas.producto import OrdenProducto


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _imagenes_orm(imagenes) -> list[ImagenProducto]:
    return [
        ImagenProducto(
            url=imagen.url,
            texto_alternativo=imagen.texto_alternativo,
            orden=imagen.orden,
            es_principal=imagen.es_principal,
        )
        for imagen in imagenes
    ]


class ProductoRepositorioSQLAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def listar(self, consulta: ProductoConsulta) -> list[ProductoAlmacenado]:
        stmt = select(Producto).where(Producto.eliminado_en.is_(None))

        if consulta.estado == EstadoFiltro.ACTIVO:
            stmt = stmt.where(Producto.estado == Estado.ACTIVO)
        elif consulta.estado == EstadoFiltro.INACTIVO:
            stmt = stmt.where(Producto.estado == Estado.INACTIVO)

        if consulta.categoria_id is not None:
            stmt = stmt.where(Producto.categoria_id == consulta.categoria_id)

        if consulta.producto_ids is not None:
            stmt = stmt.where(Producto.id.in_(consulta.producto_ids))

        if consulta.nombre:
            termino = normalizar_texto(consulta.nombre)
            if termino:
                stmt = stmt.where(
                    Producto.nombre_busqueda.ilike(f"%{termino}%")
                )

        if consulta.disponible is True:
            stmt = stmt.where(Producto.existencias > 0)
        elif consulta.disponible is False:
            stmt = stmt.where(Producto.existencias == 0)

        stmt = self._ordenar(stmt, consulta.orden)
        stmt = stmt.options(selectinload(Producto.imagenes))
        productos = self._session.scalars(stmt).all()
        return [producto_a_entidad(producto) for producto in productos]

    def obtener_por_id(self, producto_id: int) -> ProductoAlmacenado | None:
        stmt = (
            select(Producto)
            .where(
                Producto.id == producto_id,
                Producto.eliminado_en.is_(None),
            )
            .options(selectinload(Producto.imagenes))
        )
        producto = self._session.scalars(stmt).first()
        return producto_a_entidad(producto) if producto is not None else None

    def crear(self, datos: ProductoNuevo) -> ProductoAlmacenado:
        ahora = _ahora()
        producto = Producto(
            nombre=datos.nombre,
            nombre_busqueda=normalizar_texto(datos.nombre),
            slug=datos.slug,
            descripcion=datos.descripcion,
            precio=datos.precio,
            sku=datos.sku,
            categoria_id=datos.categoria_id,
            existencias=datos.existencias,
            estado=datos.estado,
            creado_en=ahora,
            actualizado_en=ahora,
            imagenes=_imagenes_orm(datos.imagenes),
        )
        self._session.add(producto)
        self._session.flush()
        return producto_a_entidad(producto)

    def reemplazar(
        self, producto_id: int, datos: ProductoReemplazo
    ) -> ProductoAlmacenado:
        stmt = (
            select(Producto)
            .where(
                Producto.id == producto_id,
                Producto.eliminado_en.is_(None),
            )
            .options(selectinload(Producto.imagenes))
        )
        producto = self._session.scalars(stmt).first()
        if producto is None:
            raise KeyError(producto_id)

        producto.nombre = datos.nombre
        producto.nombre_busqueda = normalizar_texto(datos.nombre)
        producto.slug = datos.slug
        producto.descripcion = datos.descripcion
        producto.precio = datos.precio
        producto.categoria_id = datos.categoria_id
        producto.existencias = datos.existencias
        producto.estado = datos.estado
        producto.actualizado_en = _ahora()
        producto.imagenes.clear()
        self._session.flush()
        producto.imagenes.extend(_imagenes_orm(datos.imagenes))
        self._session.flush()
        return producto_a_entidad(producto)

    def actualizar_estado(
        self, producto_id: int, estado: Estado
    ) -> ProductoAlmacenado:
        stmt = (
            select(Producto)
            .where(
                Producto.id == producto_id,
                Producto.eliminado_en.is_(None),
            )
            .options(selectinload(Producto.imagenes))
        )
        producto = self._session.scalars(stmt).first()
        if producto is None:
            raise KeyError(producto_id)
        producto.estado = estado
        producto.actualizado_en = _ahora()
        self._session.flush()
        return producto_a_entidad(producto)

    def eliminar_logico(self, producto_id: int) -> bool:
        stmt = select(Producto).where(
            Producto.id == producto_id,
            Producto.eliminado_en.is_(None),
        )
        producto = self._session.scalars(stmt).first()
        if producto is None:
            return False
        ahora = _ahora()
        producto.eliminado_en = ahora
        producto.actualizado_en = ahora
        self._session.flush()
        return True

    def existe_sku(self, sku: str, excluir_id: int | None = None) -> bool:
        objetivo = sku.strip().upper()
        condiciones = [Producto.sku == objetivo]
        if excluir_id is not None:
            condiciones.append(Producto.id != excluir_id)
        return bool(self._session.scalar(select(exists().where(*condiciones))))

    def existe_slug(self, slug: str, excluir_id: int | None = None) -> bool:
        objetivo = slug.strip().lower()
        condiciones = [Producto.slug == objetivo]
        if excluir_id is not None:
            condiciones.append(Producto.id != excluir_id)
        return bool(self._session.scalar(select(exists().where(*condiciones))))

    def contar_por_categoria(
        self,
        categoria_id: int,
        *,
        solo_activos: bool = False,
        incluir_eliminados: bool = False,
    ) -> int:
        condiciones = [Producto.categoria_id == categoria_id]
        if not incluir_eliminados:
            condiciones.append(Producto.eliminado_en.is_(None))
        if solo_activos:
            condiciones.append(Producto.estado == Estado.ACTIVO)
        return int(
            self._session.scalar(
                select(func.count(Producto.id)).where(*condiciones)
            )
            or 0
        )

    def existe_categoria_con_productos(
        self,
        categoria_id: int,
        *,
        incluir_eliminados: bool = True,
    ) -> bool:
        condiciones = [Producto.categoria_id == categoria_id]
        if not incluir_eliminados:
            condiciones.append(Producto.eliminado_en.is_(None))
        return bool(self._session.scalar(select(exists().where(*condiciones))))

    def contar_por_ids(
        self,
        producto_ids,
        *,
        solo_activos: bool = False,
        incluir_eliminados: bool = False,
    ) -> int:
        ids = set(producto_ids)
        if not ids:
            return 0
        condiciones = [Producto.id.in_(ids)]
        if not incluir_eliminados:
            condiciones.append(Producto.eliminado_en.is_(None))
        if solo_activos:
            condiciones.append(Producto.estado == Estado.ACTIVO)
        return int(
            self._session.scalar(
                select(func.count(Producto.id)).where(*condiciones)
            )
            or 0
        )

    def ids_inexistentes(self, producto_ids) -> list[int]:
        ids = set(producto_ids)
        if not ids:
            return []
        existentes = set(
            self._session.scalars(
                select(Producto.id).where(
                    Producto.id.in_(ids),
                    Producto.eliminado_en.is_(None),
                )
            ).all()
        )
        return sorted(ids - existentes)

    def _ordenar(self, stmt, orden: OrdenProducto):
        if orden == OrdenProducto.RECIENTE:
            return stmt.order_by(
                Producto.creado_en.desc(), Producto.id.desc()
            )
        if orden == OrdenProducto.NOMBRE_ASC:
            return stmt.order_by(
                Producto.nombre_busqueda.asc(), Producto.id.asc()
            )
        if orden == OrdenProducto.NOMBRE_DESC:
            return stmt.order_by(
                Producto.nombre_busqueda.desc(), Producto.id.desc()
            )
        if orden == OrdenProducto.PRECIO_ASC:
            return stmt.order_by(Producto.precio.asc(), Producto.id.asc())
        return stmt.order_by(Producto.precio.desc(), Producto.id.desc())
