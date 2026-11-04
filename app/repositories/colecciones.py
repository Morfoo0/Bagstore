import unicodedata
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from app.schemas.common import Estado, EstadoFiltro


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _fecha(dia: int, hora: int) -> datetime:
    return datetime(2026, 11, dia, hora, 0, tzinfo=timezone.utc)


def _normalizar_texto(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor.casefold())
    return "".join(
        caracter for caracter in normalizado if not unicodedata.combining(caracter)
    )


@dataclass(frozen=True, slots=True)
class ColeccionAlmacenada:
    id: int
    nombre: str
    slug: str
    estado: Estado
    producto_ids: tuple[int, ...] = ()
    descripcion: str | None = None
    imagen_portada_url: str | None = None
    creado_en: datetime = field(default_factory=_ahora)
    actualizado_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True, slots=True)
class ColeccionNueva:
    nombre: str
    slug: str
    descripcion: str | None
    estado: Estado
    imagen_portada_url: str | None
    producto_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ColeccionReemplazo:
    nombre: str
    slug: str
    descripcion: str | None
    estado: Estado
    imagen_portada_url: str | None
    producto_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ColeccionConsulta:
    nombre: str | None = None
    estado: EstadoFiltro = EstadoFiltro.ACTIVO


COLECCIONES_INICIALES = (
    ColeccionAlmacenada(
        id=1,
        nombre="La Colección",
        slug="la-coleccion",
        estado=Estado.ACTIVO,
        producto_ids=(1, 3, 6, 8),
        descripcion="Selección especial de temporada.",
        imagen_portada_url="https://cdn.bagstore.com/colecciones/la-coleccion.jpg",
        creado_en=_fecha(1, 8),
        actualizado_en=_fecha(1, 8),
    ),
    ColeccionAlmacenada(
        id=2,
        nombre="Archivo",
        slug="archivo",
        estado=Estado.INACTIVO,
        producto_ids=(2,),
        descripcion="Colección histórica fuera de temporada.",
        imagen_portada_url="https://cdn.bagstore.com/colecciones/archivo.jpg",
        creado_en=_fecha(1, 9),
        actualizado_en=_fecha(1, 9),
    ),
)


class ColeccionRepositorioMemoria:
    def __init__(
        self,
        colecciones: tuple[ColeccionAlmacenada, ...] | None = None,
    ) -> None:
        datos = colecciones if colecciones is not None else COLECCIONES_INICIALES
        self._colecciones = {coleccion.id: coleccion for coleccion in datos}
        self._siguiente_id = max(
            (coleccion.id for coleccion in datos), default=0
        ) + 1

    def listar(
        self, consulta: ColeccionConsulta | None = None
    ) -> list[ColeccionAlmacenada]:
        colecciones = list(self._colecciones.values())

        if consulta is not None:
            if consulta.estado == EstadoFiltro.ACTIVO:
                colecciones = [
                    coleccion
                    for coleccion in colecciones
                    if coleccion.estado == Estado.ACTIVO
                ]
            elif consulta.estado == EstadoFiltro.INACTIVO:
                colecciones = [
                    coleccion
                    for coleccion in colecciones
                    if coleccion.estado == Estado.INACTIVO
                ]

            if consulta.nombre:
                termino = _normalizar_texto(consulta.nombre)
                if termino:
                    colecciones = [
                        coleccion
                        for coleccion in colecciones
                        if termino in _normalizar_texto(coleccion.nombre)
                    ]

        return sorted(colecciones, key=lambda coleccion: coleccion.id)

    def obtener_por_id(self, coleccion_id: int) -> ColeccionAlmacenada | None:
        return self._colecciones.get(coleccion_id)

    def obtener_por_slug(self, slug: str) -> ColeccionAlmacenada | None:
        objetivo = slug.strip().lower()
        for coleccion in self._colecciones.values():
            if coleccion.slug == objetivo:
                return coleccion
        return None

    def crear(self, datos: ColeccionNueva) -> ColeccionAlmacenada:
        ahora = _ahora()
        coleccion = ColeccionAlmacenada(
            id=self._siguiente_id,
            nombre=datos.nombre,
            slug=datos.slug,
            estado=datos.estado,
            producto_ids=datos.producto_ids,
            descripcion=datos.descripcion,
            imagen_portada_url=datos.imagen_portada_url,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        self._colecciones[coleccion.id] = coleccion
        self._siguiente_id += 1
        return coleccion

    def reemplazar(
        self, coleccion_id: int, datos: ColeccionReemplazo
    ) -> ColeccionAlmacenada:
        actual = self._colecciones.get(coleccion_id)
        if actual is None:
            raise KeyError(coleccion_id)
        actualizada = replace(
            actual,
            nombre=datos.nombre,
            slug=datos.slug,
            estado=datos.estado,
            producto_ids=datos.producto_ids,
            descripcion=datos.descripcion,
            imagen_portada_url=datos.imagen_portada_url,
            actualizado_en=_ahora(),
        )
        self._colecciones[coleccion_id] = actualizada
        return actualizada

    def eliminar(self, coleccion_id: int) -> bool:
        return self._colecciones.pop(coleccion_id, None) is not None

    def existe_nombre(
        self, nombre: str, excluir_id: int | None = None
    ) -> bool:
        objetivo = nombre.strip().casefold()
        return any(
            coleccion.nombre.strip().casefold() == objetivo
            and coleccion.id != excluir_id
            for coleccion in self._colecciones.values()
        )

    def existe_slug(self, slug: str, excluir_id: int | None = None) -> bool:
        objetivo = slug.strip().lower()
        return any(
            coleccion.slug == objetivo and coleccion.id != excluir_id
            for coleccion in self._colecciones.values()
        )

    def listar_por_producto(
        self, producto_id: int
    ) -> list[ColeccionAlmacenada]:
        return [
            coleccion
            for coleccion in self._colecciones.values()
            if producto_id in coleccion.producto_ids
        ]

    def eliminar_producto_de_todas(self, producto_id: int) -> None:
        for coleccion_id, coleccion in list(self._colecciones.items()):
            if producto_id in coleccion.producto_ids:
                producto_ids = tuple(
                    identificador
                    for identificador in coleccion.producto_ids
                    if identificador != producto_id
                )
                self._colecciones[coleccion_id] = replace(
                    coleccion,
                    producto_ids=producto_ids,
                    actualizado_en=_ahora(),
                )
