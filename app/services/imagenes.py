from io import BytesIO
from uuid import uuid4

from PIL import Image

from app.core.errors import AppError
from app.core.storage import AlmacenamientoImagen
from app.repositories.imagenes import (
    ImagenProductoAlmacenada,
    ImagenProductoActualizacion,
    ImagenProductoNueva,
)
from app.repositories.sqlalchemy.imagenes import (
    ImagenProductoRepositorioSQLAlchemy,
)
from app.repositories.sqlalchemy.productos import (
    ProductoRepositorioSQLAlchemy,
)
from app.schemas.common import MAX_IMAGENES
from app.schemas.errors import CodigoError, ErrorDetalle
from app.schemas.imagen import ImagenProductoResponse

FORMATOS_PERMITIDOS = {
    "JPEG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
}


class ImagenProductoService:
    def __init__(
        self,
        productos: ProductoRepositorioSQLAlchemy,
        imagenes: ImagenProductoRepositorioSQLAlchemy,
        almacenamiento: AlmacenamientoImagen,
        max_image_size_bytes: int,
    ) -> None:
        self._productos = productos
        self._imagenes = imagenes
        self._almacenamiento = almacenamiento
        self._max_image_size_bytes = max_image_size_bytes

    def subir(
        self,
        producto_id: int,
        contenido: bytes,
        texto_alternativo: str | None,
        orden: int | None,
        es_principal: bool,
    ) -> ImagenProductoResponse:
        if self._productos.obtener_por_id(producto_id) is None:
            raise self._error_producto_no_encontrado(producto_id)
        if self._imagenes.contar_por_producto(producto_id) >= MAX_IMAGENES:
            raise self._error_validacion(
                "imagenes",
                f"No se permiten más de {MAX_IMAGENES} imágenes.",
            )

        extension = self._validar_archivo(contenido)
        orden_final = (
            orden
            if orden is not None
            else self._imagenes.siguiente_orden(producto_id)
        )
        if self._imagenes.existe_orden(producto_id, orden_final):
            raise self._error_validacion(
                "orden",
                "El orden indicado ya está ocupado por otra imagen.",
            )

        clave = f"productos/{producto_id}/{uuid4().hex}.{extension}"
        url = self._almacenamiento.guardar(contenido, clave)
        try:
            imagen = self._imagenes.crear(
                ImagenProductoNueva(
                    producto_id=producto_id,
                    url=url,
                    storage_key=clave,
                    texto_alternativo=(
                        texto_alternativo.strip()
                        if texto_alternativo
                        else None
                    ),
                    orden=orden_final,
                    es_principal=es_principal,
                )
            )
            if es_principal:
                self._imagenes.quitar_principal(
                    producto_id, excluir_id=imagen.id
                )
        except Exception:
            self._almacenamiento.eliminar(clave)
            raise

        self._imagenes.normalizar_principal(producto_id)
        actualizada = self._imagenes.obtener_por_id(
            producto_id, imagen.id
        )
        return self._a_response(actualizada or imagen)

    def actualizar(
        self,
        producto_id: int,
        imagen_id: int,
        texto_alternativo: str | None,
        orden: int,
        es_principal: bool,
    ) -> ImagenProductoResponse:
        if self._productos.obtener_por_id(producto_id) is None:
            raise self._error_producto_no_encontrado(producto_id)
        if self._imagenes.obtener_por_id(producto_id, imagen_id) is None:
            raise self._error_imagen_no_encontrada(imagen_id)
        if self._imagenes.existe_orden(
            producto_id, orden, excluir_id=imagen_id
        ):
            raise self._error_validacion(
                "orden",
                "El orden indicado ya está ocupado por otra imagen.",
            )

        if es_principal:
            self._imagenes.quitar_principal(
                producto_id, excluir_id=imagen_id
            )

        self._imagenes.actualizar(
            imagen_id,
            ImagenProductoActualizacion(
                texto_alternativo=(
                    texto_alternativo.strip()
                    if texto_alternativo
                    else None
                ),
                orden=orden,
                es_principal=es_principal,
            ),
        )
        self._imagenes.normalizar_principal(producto_id)
        actualizada = self._imagenes.obtener_por_id(
            producto_id, imagen_id
        )
        if actualizada is None:
            raise self._error_imagen_no_encontrada(imagen_id)
        return self._a_response(actualizada)

    def eliminar(self, producto_id: int, imagen_id: int) -> None:
        if self._productos.obtener_por_id(producto_id) is None:
            raise self._error_producto_no_encontrado(producto_id)
        imagen = self._imagenes.obtener_por_id(producto_id, imagen_id)
        if imagen is None:
            raise self._error_imagen_no_encontrada(imagen_id)
        if not self._imagenes.eliminar(imagen_id):
            raise self._error_imagen_no_encontrada(imagen_id)
        if imagen.storage_key:
            self._almacenamiento.eliminar(imagen.storage_key)
        self._imagenes.normalizar_principal(producto_id)

    def _validar_archivo(self, contenido: bytes) -> str:
        if not contenido:
            raise self._error_archivo_invalido()
        if len(contenido) > self._max_image_size_bytes:
            raise AppError(
                413,
                CodigoError.ARCHIVO_DEMASIADO_GRANDE,
                "El archivo supera el tamaño máximo permitido.",
            )
        try:
            with Image.open(BytesIO(contenido)) as imagen:
                formato = imagen.format
                imagen.verify()
        except Exception as exc:
            raise self._error_archivo_invalido() from exc
        if formato not in FORMATOS_PERMITIDOS:
            raise self._error_archivo_invalido()
        return FORMATOS_PERMITIDOS[formato]

    def _a_response(
        self, imagen: ImagenProductoAlmacenada
    ) -> ImagenProductoResponse:
        return ImagenProductoResponse(
            id=imagen.id,
            producto_id=imagen.producto_id,
            url=imagen.url,
            texto_alternativo=imagen.texto_alternativo,
            orden=imagen.orden,
            es_principal=imagen.es_principal,
            creado_en=imagen.creado_en,
            actualizado_en=imagen.actualizado_en,
        )

    def _error_producto_no_encontrado(self, producto_id: int) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe un producto con id {producto_id}.",
        )

    def _error_imagen_no_encontrada(self, imagen_id: int) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe una imagen con id {imagen_id}.",
        )

    def _error_archivo_invalido(self) -> AppError:
        return AppError(
            422,
            CodigoError.ARCHIVO_INVALIDO,
            "El archivo no es una imagen válida. Usa JPEG, PNG o WebP.",
        )

    def _error_validacion(self, campo: str, mensaje: str) -> AppError:
        return AppError(
            422,
            CodigoError.VALIDACION_FALLIDA,
            "Los datos enviados no son válidos.",
            [ErrorDetalle(campo=campo, mensaje=mensaje)],
        )
