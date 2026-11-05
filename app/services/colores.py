from app.core.errors import AppError
from app.core.text import normalizar_texto
from app.repositories.colores import (
    ColorAlmacenado,
    ColorConsulta,
    ColorNuevo,
    ColorReemplazo,
)
from app.repositories.sqlalchemy.colores import (
    ColorRepositorioSQLAlchemy,
)
from app.repositories.sqlalchemy.productos import (
    ProductoRepositorioSQLAlchemy,
)
from app.schemas.color import (
    ColoresProductoResponse,
    ColorCreate,
    ColorFiltros,
    ColorListaResponse,
    ColorResumen,
    ColorResponse,
    ColorUpdate,
    ProductoColoresUpdate,
)
from app.schemas.common import Estado, Paginacion
from app.schemas.errors import CodigoError, ErrorDetalle


class ColorService:
    def __init__(
        self,
        colores: ColorRepositorioSQLAlchemy,
        productos: ProductoRepositorioSQLAlchemy,
    ) -> None:
        self._colores = colores
        self._productos = productos

    def listar(self, filtros: ColorFiltros) -> ColorListaResponse:
        colores = self._colores.listar(
            ColorConsulta(nombre=filtros.nombre or None)
        )
        total = len(colores)
        inicio = (filtros.pagina - 1) * filtros.por_pagina
        pagina = colores[inicio : inicio + filtros.por_pagina]
        total_paginas = (
            (total + filtros.por_pagina - 1) // filtros.por_pagina
            if total
            else 0
        )
        return ColorListaResponse(
            datos=[self._a_response(color) for color in pagina],
            paginacion=Paginacion(
                pagina=filtros.pagina,
                por_pagina=filtros.por_pagina,
                total=total,
                total_paginas=total_paginas,
            ),
        )

    def obtener(self, color_id: int) -> ColorResponse:
        color = self._colores.obtener_por_id(color_id)
        if color is None:
            raise self._error_no_encontrado(color_id)
        return self._a_response(color)

    def crear(self, datos: ColorCreate) -> ColorResponse:
        if self._colores.existe_nombre(datos.nombre):
            raise self._error_conflicto(datos.nombre)
        color = self._colores.crear(
            ColorNuevo(
                nombre=datos.nombre.strip(),
                nombre_normalizado=normalizar_texto(datos.nombre),
                tono=datos.tono,
            )
        )
        return self._a_response(color)

    def actualizar(
        self, color_id: int, datos: ColorUpdate
    ) -> ColorResponse:
        if self._colores.obtener_por_id(color_id) is None:
            raise self._error_no_encontrado(color_id)
        if self._colores.existe_nombre(
            datos.nombre, excluir_id=color_id
        ):
            raise self._error_conflicto(datos.nombre)
        color = self._colores.reemplazar(
            color_id,
            ColorReemplazo(
                nombre=datos.nombre.strip(),
                nombre_normalizado=normalizar_texto(datos.nombre),
                tono=datos.tono,
            ),
        )
        return self._a_response(color)

    def eliminar(self, color_id: int) -> None:
        if self._colores.obtener_por_id(color_id) is None:
            raise self._error_no_encontrado(color_id)
        if self._colores.esta_asociado(color_id):
            raise AppError(
                409,
                CodigoError.CONFLICTO_DEPENDENCIAS,
                "No se puede eliminar el color porque tiene productos asociados.",
            )
        if not self._colores.eliminar(color_id):
            raise self._error_no_encontrado(color_id)

    def listar_por_producto(
        self,
        producto_id: int,
        es_administrador: bool = False,
    ) -> ColoresProductoResponse:
        producto = self._productos.obtener_por_id(producto_id)
        if producto is None:
            raise self._error_producto_no_encontrado(producto_id)
        if producto.estado != Estado.ACTIVO and not es_administrador:
            raise self._error_producto_no_encontrado(producto_id)
        return self._a_lista(self._colores.listar_por_producto(producto_id))

    def reemplazar_producto(
        self,
        producto_id: int,
        datos: ProductoColoresUpdate,
    ) -> ColoresProductoResponse:
        producto = self._productos.obtener_por_id(producto_id)
        if producto is None:
            raise self._error_producto_no_encontrado(producto_id)
        faltantes = [
            color_id
            for color_id in datos.color_ids
            if self._colores.obtener_por_id(color_id) is None
        ]
        if faltantes:
            raise AppError(
                422,
                CodigoError.VALIDACION_FALLIDA,
                "Los datos enviados no son válidos.",
                [
                    ErrorDetalle(
                        campo="color_ids",
                        mensaje=(
                            "No existen los colores: "
                            + ", ".join(str(color_id) for color_id in faltantes)
                            + "."
                        ),
                    )
                ],
            )
        self._colores.reemplazar_productos(producto_id, datos.color_ids)
        return self._a_lista(self._colores.listar_por_producto(producto_id))

    def _a_response(self, color: ColorAlmacenado) -> ColorResponse:
        return ColorResponse(
            id=color.id,
            nombre=color.nombre,
            tono=color.tono,
            creado_en=color.creado_en,
            actualizado_en=color.actualizado_en,
        )

    def _a_lista(
        self, colores: list[ColorAlmacenado]
    ) -> ColoresProductoResponse:
        return ColoresProductoResponse(
            datos=[
                ColorResumen(
                    id=color.id,
                    nombre=color.nombre,
                    tono=color.tono,
                )
                for color in colores
            ]
        )

    def _error_no_encontrado(self, color_id: int) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe un color con id {color_id}.",
        )

    def _error_producto_no_encontrado(self, producto_id: int) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe un producto con id {producto_id}.",
        )

    def _error_conflicto(self, nombre: str) -> AppError:
        return AppError(
            409,
            CodigoError.CONFLICTO_UNICIDAD,
            "Ya existe un color con el nombre indicado.",
            [
                ErrorDetalle(
                    campo="nombre",
                    mensaje=f"El color '{nombre}' ya está registrado.",
                )
            ],
        )
