from app.core.errors import AppError
from app.repositories.colecciones import (
    ColeccionAlmacenada,
    ColeccionConsulta,
    ColeccionNueva,
    ColeccionReemplazo,
    ColeccionRepositorioMemoria,
)
from app.repositories.productos import ProductoRepositorioMemoria
from app.schemas.coleccion import (
    ColeccionCreate,
    ColeccionFiltros,
    ColeccionListaResponse,
    ColeccionResponse,
    ColeccionUpdate,
)
from app.schemas.common import (
    Estado,
    EstadoFiltro,
    Paginacion,
    normalizar_slug,
)
from app.schemas.errors import CodigoError, ErrorDetalle


class ColeccionService:
    def __init__(
        self,
        colecciones: ColeccionRepositorioMemoria,
        productos: ProductoRepositorioMemoria,
    ) -> None:
        self._colecciones = colecciones
        self._productos = productos

    def listar(
        self,
        filtros: ColeccionFiltros,
        es_administrador: bool = False,
    ) -> ColeccionListaResponse:
        if not es_administrador and filtros.estado != EstadoFiltro.ACTIVO:
            raise self._error_acceso_denegado()

        consulta = ColeccionConsulta(
            nombre=filtros.nombre or None,
            estado=(
                filtros.estado
                if es_administrador
                else EstadoFiltro.ACTIVO
            ),
        )
        colecciones = self._colecciones.listar(consulta)
        total = len(colecciones)
        inicio = (filtros.pagina - 1) * filtros.por_pagina
        pagina = colecciones[inicio : inicio + filtros.por_pagina]
        total_paginas = (
            (total + filtros.por_pagina - 1) // filtros.por_pagina
            if total
            else 0
        )

        return ColeccionListaResponse(
            datos=[
                self._a_response(coleccion, es_administrador)
                for coleccion in pagina
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
        coleccion_id: int,
        es_administrador: bool = False,
    ) -> ColeccionResponse:
        coleccion = self._colecciones.obtener_por_id(coleccion_id)
        if coleccion is None:
            raise self._error_no_encontrado(coleccion_id)
        if coleccion.estado != Estado.ACTIVO and not es_administrador:
            raise self._error_no_encontrado(coleccion_id)
        return self._a_response(coleccion, es_administrador)

    def crear(self, datos: ColeccionCreate) -> ColeccionResponse:
        if self._colecciones.existe_nombre(datos.nombre):
            raise self._error_conflicto(
                "nombre",
                f"El nombre '{datos.nombre}' ya está registrado.",
                "Ya existe una colección con el nombre indicado.",
            )

        if datos.slug is not None:
            if self._colecciones.existe_slug(datos.slug):
                raise self._error_conflicto(
                    "slug",
                    f"El slug '{datos.slug}' ya está registrado.",
                    "Ya existe una colección con el slug indicado.",
                )
            slug = datos.slug
        else:
            slug = self._generar_slug(datos.nombre)

        producto_ids = self._validar_producto_ids(
            datos.producto_ids or []
        )
        coleccion = self._colecciones.crear(
            ColeccionNueva(
                nombre=datos.nombre,
                slug=slug,
                descripcion=datos.descripcion,
                estado=datos.estado,
                imagen_portada_url=datos.imagen_portada_url,
                producto_ids=producto_ids,
            )
        )
        return self._a_response(coleccion, es_administrador=True)

    def actualizar(
        self,
        coleccion_id: int,
        datos: ColeccionUpdate,
    ) -> ColeccionResponse:
        actual = self._colecciones.obtener_por_id(coleccion_id)
        if actual is None:
            raise self._error_no_encontrado(coleccion_id)

        if self._colecciones.existe_nombre(
            datos.nombre, excluir_id=coleccion_id
        ):
            raise self._error_conflicto(
                "nombre",
                f"El nombre '{datos.nombre}' ya está registrado.",
                "Ya existe una colección con el nombre indicado.",
            )

        if datos.slug is None:
            slug = actual.slug
        else:
            if self._colecciones.existe_slug(
                datos.slug, excluir_id=coleccion_id
            ):
                raise self._error_conflicto(
                    "slug",
                    f"El slug '{datos.slug}' ya está registrado.",
                    "Ya existe una colección con el slug indicado.",
                )
            slug = datos.slug

        producto_ids = self._validar_producto_ids(datos.producto_ids)
        coleccion = self._colecciones.reemplazar(
            coleccion_id,
            ColeccionReemplazo(
                nombre=datos.nombre,
                slug=slug,
                descripcion=datos.descripcion,
                estado=datos.estado,
                imagen_portada_url=datos.imagen_portada_url,
                producto_ids=producto_ids,
            ),
        )
        return self._a_response(coleccion, es_administrador=True)

    def eliminar(self, coleccion_id: int) -> None:
        if self._colecciones.obtener_por_id(coleccion_id) is None:
            raise self._error_no_encontrado(coleccion_id)
        if not self._colecciones.eliminar(coleccion_id):
            raise self._error_no_encontrado(coleccion_id)

    def _validar_producto_ids(
        self, producto_ids: list[int]
    ) -> tuple[int, ...]:
        inexistentes = self._productos.ids_inexistentes(producto_ids)
        if inexistentes:
            listado = ", ".join(str(producto_id) for producto_id in inexistentes)
            raise self._error_validacion(
                "producto_ids",
                f"Los siguientes productos no existen o están eliminados: {listado}.",
            )
        return tuple(producto_ids)

    def _a_response(
        self,
        coleccion: ColeccionAlmacenada,
        es_administrador: bool,
    ) -> ColeccionResponse:
        total_productos = self._productos.contar_por_ids(
            coleccion.producto_ids,
            solo_activos=not es_administrador,
        )
        return ColeccionResponse(
            id=coleccion.id,
            nombre=coleccion.nombre,
            slug=coleccion.slug,
            descripcion=coleccion.descripcion,
            estado=coleccion.estado,
            imagen_portada_url=coleccion.imagen_portada_url,
            total_productos=total_productos,
            creado_en=coleccion.creado_en,
            actualizado_en=coleccion.actualizado_en,
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
        while self._colecciones.existe_slug(candidato):
            candidato = f"{base}-{sufijo}"
            sufijo += 1
        return candidato

    def _error_no_encontrado(self, coleccion_id: int) -> AppError:
        return AppError(
            404,
            CodigoError.RECURSO_NO_ENCONTRADO,
            f"No existe una colección con id {coleccion_id}.",
        )

    def _error_acceso_denegado(self) -> AppError:
        return AppError(
            403,
            CodigoError.ACCESO_DENEGADO,
            "Se requiere el rol administrador para consultar colecciones inactivas.",
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
