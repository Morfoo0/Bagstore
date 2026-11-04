from app.core.errors import AppError
from app.repositories.categorias import (
    CategoriaAlmacenada,
    CategoriaConsulta,
    CategoriaNueva,
    CategoriaReemplazo,
    CategoriaRepositorioMemoria,
)
from app.repositories.productos import ProductoRepositorioMemoria
from app.schemas.categoria import (
    CategoriaCreate,
    CategoriaFiltros,
    CategoriaListaResponse,
    CategoriaResponse,
    CategoriaUpdate,
)
from app.schemas.common import (
    Estado,
    EstadoFiltro,
    Paginacion,
    normalizar_slug,
)
from app.schemas.errors import CodigoError, ErrorDetalle


class CategoriaService:
    def __init__(
        self,
        categorias: CategoriaRepositorioMemoria,
        productos: ProductoRepositorioMemoria,
    ) -> None:
        self._categorias = categorias
        self._productos = productos

    def listar(
        self,
        filtros: CategoriaFiltros,
        es_administrador: bool = False,
    ) -> CategoriaListaResponse:
        if not es_administrador and filtros.estado != EstadoFiltro.ACTIVO:
            raise self._error_acceso_denegado()

        consulta = CategoriaConsulta(
            nombre=filtros.nombre or None,
            estado=(
                filtros.estado
                if es_administrador
                else EstadoFiltro.ACTIVO
            ),
        )
        categorias = self._categorias.listar(consulta)
        total = len(categorias)
        inicio = (filtros.pagina - 1) * filtros.por_pagina
        pagina = categorias[inicio : inicio + filtros.por_pagina]
        total_paginas = (
            (total + filtros.por_pagina - 1) // filtros.por_pagina
            if total
            else 0
        )

        return CategoriaListaResponse(
            datos=[
                self._a_response(categoria, es_administrador)
                for categoria in pagina
            ],
            paginacion=Paginacion(
                pagina=filtros.pagina,
                por_pagina=filtros.por_pagina,
                total=total,
                total_paginas=total_paginas,
            ),
        )

    def obtener(
        self,
        categoria_id: int,
        es_administrador: bool = False,
    ) -> CategoriaResponse:
        categoria = self._categorias.obtener_por_id(categoria_id)
        if categoria is None:
            raise self._error_no_encontrado(categoria_id)
        if categoria.estado != Estado.ACTIVO and not es_administrador:
            raise self._error_no_encontrado(categoria_id)
        return self._a_response(categoria, es_administrador)

    def crear(self, datos: CategoriaCreate) -> CategoriaResponse:
        if self._categorias.existe_nombre(datos.nombre):
            raise self._error_conflicto(
                "nombre",
                f"El nombre '{datos.nombre}' ya está registrado.",
                "Ya existe una categoría con el nombre indicado.",
            )

        if datos.slug is not None:
            if self._categorias.existe_slug(datos.slug):
                raise self._error_conflicto(
                    "slug",
                    f"El slug '{datos.slug}' ya está registrado.",
                    "Ya existe una categoría con el slug indicado.",
                )
            slug = datos.slug
        else:
            slug = self._generar_slug(datos.nombre)

        categoria = self._categorias.crear(
            CategoriaNueva(
                nombre=datos.nombre,
                slug=slug,
                descripcion=datos.descripcion,
                estado=datos.estado,
                orden=datos.orden,
            )
        )
        return self._a_response(categoria, es_administrador=True)

    def actualizar(
        self,
        categoria_id: int,
        datos: CategoriaUpdate,
    ) -> CategoriaResponse:
        actual = self._categorias.obtener_por_id(categoria_id)
        if actual is None:
            raise self._error_no_encontrado(categoria_id)

        if self._categorias.existe_nombre(
            datos.nombre, excluir_id=categoria_id
        ):
            raise self._error_conflicto(
                "nombre",
                f"El nombre '{datos.nombre}' ya está registrado.",
                "Ya existe una categoría con el nombre indicado.",
            )

        if datos.slug is None:
            slug = actual.slug
        else:
            if self._categorias.existe_slug(
                datos.slug, excluir_id=categoria_id
            ):
                raise self._error_conflicto(
                    "slug",
                    f"El slug '{datos.slug}' ya está registrado.",
                    "Ya existe una categoría con el slug indicado.",
                )
            slug = datos.slug

        if (
            datos.estado == Estado.INACTIVO
            and self._productos.contar_por_categoria(
                categoria_id,
                solo_activos=True,
            )
            > 0
        ):
            raise self._error_dependencias(
                "No se puede desactivar la categoría porque tiene productos activos."
            )

        categoria = self._categorias.reemplazar(
            categoria_id,
            CategoriaReemplazo(
                nombre=datos.nombre,
                slug=slug,
                descripcion=datos.descripcion,
                estado=datos.estado,
                orden=datos.orden,
            ),
        )
        return self._a_response(categoria, es_administrador=True)

    def eliminar(self, categoria_id: int) -> None:
        if self._categorias.obtener_por_id(categoria_id) is None:
            raise self._error_no_encontrado(categoria_id)
        if self._productos.existe_categoria_con_productos(categoria_id):
            raise self._error_dependencias(
                "No se puede eliminar la categoría porque tiene productos asociados."
            )
        if not self._categorias.eliminar(categoria_id):
            raise self._error_no_encontrado(categoria_id)

    def _a_response(
        self,
        categoria: CategoriaAlmacenada,
        es_administrador: bool,
    ) -> CategoriaResponse:
        total_productos = self._productos.contar_por_categoria(
            categoria.id,
            solo_activos=not es_administrador,
        )
        return CategoriaResponse(
            id=categoria.id,
            nombre=categoria.nombre,
            slug=categoria.slug,
            descripcion=categoria.descripcion,
            estado=categoria.estado,
            orden=categoria.orden,
            total_productos=total_productos,
            creado_en=categoria.creado_en,
            actualizado_en=categoria.actualizado_en,
        )

    def _generar_slug(self, nombre: str) -> str:
        base = normalizar_slug(nombre)
        if not base:
            raise self._error_validacion(
                "slug",
                "No se pudo generar un slug a partir del nombre.",
            )
        candidato = base
        sufijo = 2
        while self._categorias.existe_slug(candidato):
            candidato = f"{base}-{sufijo}"
            sufijo += 1
        return candidato

    def _error_no_encontrado(self, categoria_id: int) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe una categoría con id {categoria_id}.",
        )

    def _error_acceso_denegado(self) -> AppError:
        return AppError(
            403,
            CodigoError.ACCESO_DENEGADO,
            "Se requiere el rol administrador para consultar categorías inactivas.",
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

    def _error_dependencias(self, mensaje: str) -> AppError:
        return AppError(
            409,
            CodigoError.CONFLICTO_DEPENDENCIAS,
            mensaje,
        )
