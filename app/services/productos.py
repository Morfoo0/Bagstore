from app.core.errors import AppError
from app.repositories.categorias import CategoriaRepositorioMemoria
from app.repositories.colecciones import ColeccionRepositorioMemoria
from app.repositories.sqlalchemy.colores import ColorRepositorioSQLAlchemy
from app.repositories.productos import (
    ImagenAlmacenada,
    ProductoAlmacenado,
    ProductoConsulta,
    ProductoNuevo,
    ProductoReemplazo,
    ProductoRepositorioMemoria,
)
from app.schemas.categoria import CategoriaResumen
from app.schemas.coleccion import ColeccionResumen
from app.schemas.common import (
    Estado,
    EstadoFiltro,
    Paginacion,
    normalizar_slug,
)
from app.schemas.errors import CodigoError, ErrorDetalle
from app.schemas.imagen import ImagenCreate, ImagenResponse
from app.schemas.producto import (
    ProductoCreate,
    ProductoFiltros,
    ProductoListaResponse,
    ProductoResumen,
    ProductoResponse,
    ProductosDeColeccionFiltros,
    ProductoUpdate,
)


class ProductoService:
    def __init__(
        self,
        productos: ProductoRepositorioMemoria,
        categorias: CategoriaRepositorioMemoria,
        colecciones: ColeccionRepositorioMemoria,
        colores: ColorRepositorioSQLAlchemy | None = None,
    ) -> None:
        self._productos = productos
        self._categorias = categorias
        self._colecciones = colecciones
        self._colores = colores

    def listar(
        self,
        filtros: ProductoFiltros,
        es_administrador: bool = False,
    ) -> ProductoListaResponse:
        try:
            filtros.validar_combinaciones()
        except ValueError as exc:
            raise AppError(
                400,
                CodigoError.SOLICITUD_INVALIDA,
                str(exc),
            ) from exc

        if not es_administrador and filtros.estado != EstadoFiltro.ACTIVO:
            raise AppError(
                403,
                CodigoError.ACCESO_DENEGADO,
                "Se requiere el rol administrador para consultar productos inactivos.",
            )

        categoria_id, categoria_valida = self._resolver_categoria(
            filtros, es_administrador
        )
        if not categoria_valida:
            return self._respuesta_vacia(filtros)

        producto_ids, coleccion_valida = self._resolver_coleccion(
            filtros, es_administrador
        )
        if not coleccion_valida:
            return self._respuesta_vacia(filtros)

        color_ids, color_valido = self._resolver_color(filtros)
        if not color_valido:
            return self._respuesta_vacia(filtros)
        producto_ids = self._combinar_ids(producto_ids, color_ids)

        consulta = ProductoConsulta(
            categoria_id=categoria_id,
            producto_ids=producto_ids,
            nombre=filtros.nombre or None,
            disponible=filtros.disponible,
            estado=(
                filtros.estado
                if es_administrador
                else EstadoFiltro.ACTIVO
            ),
            orden=filtros.orden,
        )
        productos = self._productos.listar(consulta)
        total = len(productos)
        inicio = (filtros.pagina - 1) * filtros.por_pagina
        pagina = productos[inicio : inicio + filtros.por_pagina]
        total_paginas = (
            (total + filtros.por_pagina - 1) // filtros.por_pagina
            if total
            else 0
        )

        return ProductoListaResponse(
            datos=[
                self._a_resumen(producto) for producto in pagina
            ],
            paginacion=Paginacion(
                pagina=filtros.pagina,
                por_pagina=filtros.por_pagina,
                total=total,
                total_paginas=total_paginas,
            ),
        )

    def listar_por_coleccion(
        self,
        coleccion_id: int,
        filtros: ProductosDeColeccionFiltros,
        es_administrador: bool = True,
    ) -> ProductoListaResponse:
        coleccion = self._colecciones.obtener_por_id(coleccion_id)
        if coleccion is None:
            raise self._error_coleccion_no_encontrada(coleccion_id)
        if not es_administrador and coleccion.estado != Estado.ACTIVO:
            raise self._error_coleccion_no_encontrada(coleccion_id)

        filtros_producto = ProductoFiltros(
            coleccion_id=coleccion_id,
            nombre=filtros.nombre or None,
            disponible=filtros.disponible,
            estado=filtros.estado,
            pagina=filtros.pagina,
            por_pagina=filtros.por_pagina,
            orden=filtros.orden,
        )
        return self.listar(
            filtros_producto,
            es_administrador=es_administrador,
        )

    def obtener(
        self,
        producto_id: int,
        es_administrador: bool = False,
    ) -> ProductoResponse:
        producto = self._productos.obtener_por_id(producto_id)
        if producto is None:
            raise self._error_no_encontrado(producto_id)
        if producto.estado != Estado.ACTIVO and not es_administrador:
            raise self._error_no_encontrado(producto_id)
        return self._a_detalle(producto, es_administrador)

    def crear(self, datos: ProductoCreate) -> ProductoResponse:
        categoria = self._categorias.obtener_por_id(datos.categoria_id)
        if categoria is None:
            raise self._error_validacion(
                "categoria_id",
                "La categoría indicada no existe.",
            )
        if datos.estado == Estado.ACTIVO and categoria.estado != Estado.ACTIVO:
            raise self._error_validacion(
                "categoria_id",
                "La categoría está inactiva y el producto no puede estar activo.",
            )

        if self._productos.existe_sku(datos.sku):
            raise self._error_conflicto(
                "sku",
                f"El SKU '{datos.sku}' ya está registrado.",
                "Ya existe un producto con el SKU indicado.",
            )

        if datos.slug is not None:
            if self._productos.existe_slug(datos.slug):
                raise self._error_conflicto(
                    "slug",
                    f"El slug '{datos.slug}' ya está registrado.",
                    "Ya existe un producto con el slug indicado.",
                )
            slug = datos.slug
        else:
            slug = self._generar_slug(datos.nombre)

        producto = self._productos.crear(
            ProductoNuevo(
                nombre=datos.nombre,
                slug=slug,
                descripcion=datos.descripcion,
                precio=datos.precio,
                sku=datos.sku,
                categoria_id=datos.categoria_id,
                existencias=datos.existencias,
                imagenes=self._imagenes_almacenadas(datos.imagenes),
                estado=datos.estado,
            )
        )
        return self._a_detalle(producto, es_administrador=False)

    def actualizar(
        self,
        producto_id: int,
        datos: ProductoUpdate,
    ) -> ProductoResponse:
        actual = self._productos.obtener_por_id(producto_id)
        if actual is None:
            raise self._error_no_encontrado(producto_id)

        categoria = self._categorias.obtener_por_id(datos.categoria_id)
        if categoria is None:
            raise self._error_validacion(
                "categoria_id",
                "La categoría indicada no existe.",
            )
        if datos.estado == Estado.ACTIVO and categoria.estado != Estado.ACTIVO:
            raise self._error_validacion(
                "categoria_id",
                "La categoría está inactiva y el producto no puede estar activo.",
            )

        if datos.sku is not None and datos.sku != actual.sku:
            raise self._error_validacion(
                "sku",
                "El SKU no se puede modificar después de crear el producto.",
            )

        if datos.slug is None:
            slug = actual.slug
        else:
            if self._productos.existe_slug(
                datos.slug, excluir_id=producto_id
            ):
                raise self._error_conflicto(
                    "slug",
                    f"El slug '{datos.slug}' ya está registrado.",
                    "Ya existe un producto con el slug indicado.",
                )
            slug = datos.slug

        producto = self._productos.reemplazar(
            producto_id,
            ProductoReemplazo(
                nombre=datos.nombre,
                slug=slug,
                descripcion=datos.descripcion,
                precio=datos.precio,
                categoria_id=datos.categoria_id,
                existencias=datos.existencias,
                imagenes=self._imagenes_almacenadas(datos.imagenes),
                estado=datos.estado,
            ),
        )
        return self._a_detalle(producto, es_administrador=False)

    def cambiar_estado(
        self, producto_id: int, estado: Estado
    ) -> ProductoResponse:
        producto = self._productos.obtener_por_id(producto_id)
        if producto is None:
            raise self._error_no_encontrado(producto_id)
        if estado == Estado.ACTIVO:
            categoria = self._categorias.obtener_por_id(
                producto.categoria_id
            )
            if categoria is None:
                raise self._error_validacion(
                    "categoria_id",
                    "La categoría indicada no existe.",
                )
            if categoria.estado != Estado.ACTIVO:
                raise self._error_validacion(
                    "categoria_id",
                    "La categoría está inactiva y el producto no puede estar activo.",
                )
        actualizado = self._productos.actualizar_estado(
            producto_id, estado
        )
        return self._a_detalle(actualizado, es_administrador=True)

    def eliminar(self, producto_id: int) -> None:
        if not self._productos.eliminar_logico(producto_id):
            raise self._error_no_encontrado(producto_id)
        self._colecciones.eliminar_producto_de_todas(producto_id)

    def _resolver_categoria(
        self,
        filtros: ProductoFiltros,
        es_administrador: bool,
    ) -> tuple[int | None, bool]:
        if filtros.categoria_id is not None:
            categoria = self._categorias.obtener_por_id(filtros.categoria_id)
        elif filtros.categoria is not None:
            categoria = self._categorias.obtener_por_slug(filtros.categoria)
        else:
            return None, True

        if categoria is None:
            return None, False
        if not es_administrador and categoria.estado != Estado.ACTIVO:
            return None, False
        return categoria.id, True

    def _resolver_coleccion(
        self,
        filtros: ProductoFiltros,
        es_administrador: bool,
    ) -> tuple[frozenset[int] | None, bool]:
        if filtros.coleccion_id is not None:
            coleccion = self._colecciones.obtener_por_id(filtros.coleccion_id)
        elif filtros.coleccion is not None:
            coleccion = self._colecciones.obtener_por_slug(filtros.coleccion)
        else:
            return None, True

        if coleccion is None:
            return None, False
        if not es_administrador and coleccion.estado != Estado.ACTIVO:
            return None, False
        return frozenset(coleccion.producto_ids), True

    def _resolver_color(
        self,
        filtros: ProductoFiltros,
    ) -> tuple[frozenset[int] | None, bool]:
        if filtros.color_id is None:
            return None, True
        if self._colores is None:
            return None, False
        color = self._colores.obtener_por_id(filtros.color_id)
        if color is None:
            return None, False
        return frozenset(color.producto_ids), True

    def _combinar_ids(
        self,
        *conjuntos: frozenset[int] | None,
    ) -> frozenset[int] | None:
        presentes = [
            conjunto for conjunto in conjuntos if conjunto is not None
        ]
        if not presentes:
            return None
        resultado = presentes[0]
        for conjunto in presentes[1:]:
            resultado = resultado & conjunto
        return frozenset(resultado)

    def _generar_slug(self, nombre: str) -> str:
        base = normalizar_slug(nombre)
        if not base:
            raise self._error_validacion(
                "slug",
                "No se pudo generar un slug a partir del nombre.",
            )
        candidato = base
        sufijo = 2
        while self._productos.existe_slug(candidato):
            candidato = f"{base}-{sufijo}"
            sufijo += 1
        return candidato

    def _respuesta_vacia(
        self, filtros: ProductoFiltros
    ) -> ProductoListaResponse:
        return ProductoListaResponse(
            datos=[],
            paginacion=Paginacion(
                pagina=filtros.pagina,
                por_pagina=filtros.por_pagina,
                total=0,
                total_paginas=0,
            ),
        )

    def _a_resumen(
        self,
        producto: ProductoAlmacenado,
    ) -> ProductoResumen:
        return ProductoResumen(
            id=producto.id,
            nombre=producto.nombre,
            slug=producto.slug,
            precio=producto.precio,
            disponible=producto.disponible,
            estado=producto.estado,
            imagen_principal=self._imagen_principal(producto),
            categoria=self._categoria_resumen(producto.categoria_id),
        )

    def _a_detalle(
        self,
        producto: ProductoAlmacenado,
        es_administrador: bool,
    ) -> ProductoResponse:
        colecciones = self._colecciones.listar_por_producto(producto.id)
        if not es_administrador:
            colecciones = [
                coleccion
                for coleccion in colecciones
                if coleccion.estado == Estado.ACTIVO
            ]
        colecciones.sort(key=lambda coleccion: coleccion.id)

        return ProductoResponse(
            id=producto.id,
            nombre=producto.nombre,
            slug=producto.slug,
            descripcion=producto.descripcion,
            precio=producto.precio,
            sku=producto.sku,
            categoria=self._categoria_resumen(producto.categoria_id),
            colecciones=[
                ColeccionResumen(
                    id=coleccion.id,
                    nombre=coleccion.nombre,
                    slug=coleccion.slug,
                )
                for coleccion in colecciones
            ],
            existencias=producto.existencias,
            disponible=producto.disponible,
            imagenes=[
                self._a_imagen(imagen) for imagen in producto.imagenes
            ],
            estado=producto.estado,
            creado_en=producto.creado_en,
            actualizado_en=producto.actualizado_en,
        )

    def _categoria_resumen(self, categoria_id: int) -> CategoriaResumen:
        categoria = self._categorias.obtener_por_id(categoria_id)
        if categoria is None:
            raise AppError(
                500,
                CodigoError.ERROR_INTERNO,
                "La categoría asociada al producto no existe.",
            )
        return CategoriaResumen(
            id=categoria.id,
            nombre=categoria.nombre,
            slug=categoria.slug,
        )

    def _imagen_principal(
        self, producto: ProductoAlmacenado
    ) -> ImagenResponse | None:
        if not producto.imagenes:
            return None
        principal = next(
            (
                imagen
                for imagen in producto.imagenes
                if imagen.es_principal
            ),
            producto.imagenes[0],
        )
        return self._a_imagen(principal)

    def _a_imagen(self, imagen: ImagenAlmacenada) -> ImagenResponse:
        return ImagenResponse(
            url=imagen.url,
            texto_alternativo=imagen.texto_alternativo,
            orden=imagen.orden,
            es_principal=imagen.es_principal,
        )

    def _imagenes_almacenadas(
        self, imagenes: list[ImagenCreate]
    ) -> tuple[ImagenAlmacenada, ...]:
        return tuple(
            ImagenAlmacenada(
                url=imagen.url,
                texto_alternativo=imagen.texto_alternativo,
                orden=imagen.orden if imagen.orden is not None else indice + 1,
                es_principal=imagen.es_principal,
            )
            for indice, imagen in enumerate(imagenes)
        )

    def _error_no_encontrado(self, producto_id: int) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe un producto con id {producto_id}.",
        )

    def _error_coleccion_no_encontrada(
        self, coleccion_id: int
    ) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe una colección con id {coleccion_id}.",
        )

    def _error_validacion(self, campo: str, mensaje: str) -> AppError:
        return AppError(
            422,
            CodigoError.VALIDACION_FALLIDA,
            "Los datos enviados no son válidos.",
            [ErrorDetalle(campo=campo, mensaje=mensaje)],
        )

    def _error_conflicto(
        self,
        campo: str,
        detalle: str,
        mensaje: str,
    ) -> AppError:
        return AppError(
            409,
            CodigoError.CONFLICTO_UNICIDAD,
            mensaje,
            [ErrorDetalle(campo=campo, mensaje=detalle)],
        )
