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
class CategoriaAlmacenada:
    id: int
    nombre: str
    slug: str
    estado: Estado
    descripcion: str | None = None
    orden: int = 0
    creado_en: datetime = field(default_factory=_ahora)
    actualizado_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True, slots=True)
class CategoriaNueva:
    nombre: str
    slug: str
    descripcion: str | None
    estado: Estado
    orden: int


@dataclass(frozen=True, slots=True)
class CategoriaReemplazo:
    nombre: str
    slug: str
    descripcion: str | None
    estado: Estado
    orden: int


@dataclass(frozen=True, slots=True)
class CategoriaConsulta:
    nombre: str | None = None
    estado: EstadoFiltro = EstadoFiltro.ACTIVO


CATEGORIAS_INICIALES = (
    CategoriaAlmacenada(
        id=1,
        nombre="Cross Body",
        slug="cross-body",
        estado=Estado.ACTIVO,
        descripcion="Bolsas cross body y bandoleras.",
        orden=2,
        creado_en=_fecha(1, 9),
        actualizado_en=_fecha(1, 9),
    ),
    CategoriaAlmacenada(
        id=2,
        nombre="Tote Bags",
        slug="tote-bags",
        estado=Estado.ACTIVO,
        descripcion="Bolsas tote.",
        orden=1,
        creado_en=_fecha(1, 8),
        actualizado_en=_fecha(1, 8),
    ),
    CategoriaAlmacenada(
        id=3,
        nombre="Mini Bags",
        slug="mini-bags",
        estado=Estado.ACTIVO,
        descripcion="Bolsas mini.",
        orden=3,
        creado_en=_fecha(1, 10),
        actualizado_en=_fecha(1, 10),
    ),
)


class CategoriaRepositorioMemoria:
    def __init__(
        self,
        categorias: tuple[CategoriaAlmacenada, ...] | None = None,
    ) -> None:
        datos = categorias if categorias is not None else CATEGORIAS_INICIALES
        self._categorias = {categoria.id: categoria for categoria in datos}
        self._siguiente_id = max(
            (categoria.id for categoria in datos), default=0
        ) + 1

    def listar(
        self, consulta: CategoriaConsulta | None = None
    ) -> list[CategoriaAlmacenada]:
        categorias = list(self._categorias.values())

        if consulta is not None:
            if consulta.estado == EstadoFiltro.ACTIVO:
                categorias = [
                    categoria
                    for categoria in categorias
                    if categoria.estado == Estado.ACTIVO
                ]
            elif consulta.estado == EstadoFiltro.INACTIVO:
                categorias = [
                    categoria
                    for categoria in categorias
                    if categoria.estado == Estado.INACTIVO
                ]

            if consulta.nombre:
                termino = _normalizar_texto(consulta.nombre)
                if termino:
                    categorias = [
                        categoria
                        for categoria in categorias
                        if termino in _normalizar_texto(categoria.nombre)
                    ]

        return sorted(categorias, key=lambda categoria: (categoria.orden, categoria.id))

    def obtener_por_id(self, categoria_id: int) -> CategoriaAlmacenada | None:
        return self._categorias.get(categoria_id)

    def obtener_por_slug(self, slug: str) -> CategoriaAlmacenada | None:
        objetivo = slug.strip().lower()
        for categoria in self._categorias.values():
            if categoria.slug == objetivo:
                return categoria
        return None

    def crear(self, datos: CategoriaNueva) -> CategoriaAlmacenada:
        ahora = _ahora()
        categoria = CategoriaAlmacenada(
            id=self._siguiente_id,
            nombre=datos.nombre,
            slug=datos.slug,
            estado=datos.estado,
            descripcion=datos.descripcion,
            orden=datos.orden,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        self._categorias[categoria.id] = categoria
        self._siguiente_id += 1
        return categoria

    def reemplazar(
        self, categoria_id: int, datos: CategoriaReemplazo
    ) -> CategoriaAlmacenada:
        actual = self._categorias.get(categoria_id)
        if actual is None:
            raise KeyError(categoria_id)
        actualizada = replace(
            actual,
            nombre=datos.nombre,
            slug=datos.slug,
            estado=datos.estado,
            descripcion=datos.descripcion,
            orden=datos.orden,
            actualizado_en=_ahora(),
        )
        self._categorias[categoria_id] = actualizada
        return actualizada

    def eliminar(self, categoria_id: int) -> bool:
        return self._categorias.pop(categoria_id, None) is not None

    def existe_nombre(
        self, nombre: str, excluir_id: int | None = None
    ) -> bool:
        objetivo = nombre.strip().casefold()
        return any(
            categoria.nombre.strip().casefold() == objetivo
            and categoria.id != excluir_id
            for categoria in self._categorias.values()
        )

    def existe_slug(self, slug: str, excluir_id: int | None = None) -> bool:
        objetivo = slug.strip().lower()
        return any(
            categoria.slug == objetivo and categoria.id != excluir_id
            for categoria in self._categorias.values()
        )
