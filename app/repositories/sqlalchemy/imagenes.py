from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.imagen import ImagenProducto
from app.repositories.imagenes import (
    ImagenProductoActualizacion,
    ImagenProductoAlmacenada,
    ImagenProductoNueva,
)


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _a_entidad(imagen: ImagenProducto) -> ImagenProductoAlmacenada:
    return ImagenProductoAlmacenada(
        id=imagen.id,
        producto_id=imagen.producto_id,
        url=imagen.url,
        storage_key=imagen.storage_key,
        texto_alternativo=imagen.texto_alternativo,
        orden=imagen.orden,
        es_principal=imagen.es_principal,
        creado_en=imagen.creado_en,
        actualizado_en=imagen.actualizado_en,
    )


class ImagenProductoRepositorioSQLAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def listar_por_producto(
        self, producto_id: int
    ) -> list[ImagenProductoAlmacenada]:
        stmt = (
            select(ImagenProducto)
            .where(ImagenProducto.producto_id == producto_id)
            .order_by(ImagenProducto.orden.asc(), ImagenProducto.id.asc())
        )
        imagenes = self._session.scalars(stmt).all()
        return [_a_entidad(imagen) for imagen in imagenes]

    def obtener_por_id(
        self, producto_id: int, imagen_id: int
    ) -> ImagenProductoAlmacenada | None:
        imagen = self._session.scalars(
            select(ImagenProducto).where(
                ImagenProducto.id == imagen_id,
                ImagenProducto.producto_id == producto_id,
            )
        ).first()
        return _a_entidad(imagen) if imagen is not None else None

    def crear(
        self, datos: ImagenProductoNueva
    ) -> ImagenProductoAlmacenada:
        ahora = _ahora()
        imagen = ImagenProducto(
            producto_id=datos.producto_id,
            url=datos.url,
            storage_key=datos.storage_key,
            texto_alternativo=datos.texto_alternativo,
            orden=datos.orden,
            es_principal=datos.es_principal,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        self._session.add(imagen)
        self._session.flush()
        return _a_entidad(imagen)

    def actualizar(
        self,
        imagen_id: int,
        datos: ImagenProductoActualizacion,
    ) -> ImagenProductoAlmacenada:
        imagen = self._session.get(ImagenProducto, imagen_id)
        if imagen is None:
            raise KeyError(imagen_id)
        imagen.texto_alternativo = datos.texto_alternativo
        imagen.orden = datos.orden
        imagen.es_principal = datos.es_principal
        imagen.actualizado_en = _ahora()
        self._session.flush()
        return _a_entidad(imagen)

    def eliminar(self, imagen_id: int) -> bool:
        imagen = self._session.get(ImagenProducto, imagen_id)
        if imagen is None:
            return False
        self._session.delete(imagen)
        self._session.flush()
        return True

    def contar_por_producto(self, producto_id: int) -> int:
        return int(
            self._session.scalar(
                select(func.count(ImagenProducto.id)).where(
                    ImagenProducto.producto_id == producto_id
                )
            )
            or 0
        )

    def siguiente_orden(self, producto_id: int) -> int:
        maximo = self._session.scalar(
            select(func.max(ImagenProducto.orden)).where(
                ImagenProducto.producto_id == producto_id
            )
        )
        return int(maximo or 0) + 1

    def existe_orden(
        self,
        producto_id: int,
        orden: int,
        excluir_id: int | None = None,
    ) -> bool:
        stmt = select(ImagenProducto).where(
            ImagenProducto.producto_id == producto_id,
            ImagenProducto.orden == orden,
        )
        if excluir_id is not None:
            stmt = stmt.where(ImagenProducto.id != excluir_id)
        return self._session.scalars(stmt).first() is not None

    def quitar_principal(
        self, producto_id: int, excluir_id: int | None = None
    ) -> None:
        stmt = select(ImagenProducto).where(
            ImagenProducto.producto_id == producto_id,
            ImagenProducto.es_principal.is_(True),
        )
        if excluir_id is not None:
            stmt = stmt.where(ImagenProducto.id != excluir_id)
        for imagen in self._session.scalars(stmt).all():
            imagen.es_principal = False
            imagen.actualizado_en = _ahora()
        self._session.flush()

    def marcar_principal(self, imagen_id: int) -> None:
        imagen = self._session.get(ImagenProducto, imagen_id)
        if imagen is None:
            return
        imagen.es_principal = True
        imagen.actualizado_en = _ahora()
        self._session.flush()

    def normalizar_principal(self, producto_id: int) -> None:
        imagenes = self.listar_por_producto(producto_id)
        if not imagenes:
            return
        principales = [imagen for imagen in imagenes if imagen.es_principal]
        if len(principales) == 1:
            return
        if len(principales) > 1:
            conservar = min(principales, key=lambda imagen: imagen.orden)
            for imagen in principales:
                if imagen.id != conservar.id:
                    self._actualizar_principal(imagen.id, False)
            return
        self._actualizar_principal(imagenes[0].id, True)

    def _actualizar_principal(self, imagen_id: int, valor: bool) -> None:
        imagen = self._session.get(ImagenProducto, imagen_id)
        if imagen is None:
            return
        imagen.es_principal = valor
        imagen.actualizado_en = _ahora()
        self._session.flush()
