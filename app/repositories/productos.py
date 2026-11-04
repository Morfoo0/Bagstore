import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal

from app.schemas.common import Estado, EstadoFiltro
from app.schemas.producto import OrdenProducto


@dataclass(frozen=True, slots=True)
class ImagenAlmacenada:
    url: str
    texto_alternativo: str | None
    orden: int
    es_principal: bool


@dataclass(frozen=True, slots=True)
class ProductoAlmacenado:
    id: int
    nombre: str
    slug: str
    descripcion: str | None
    precio: Decimal
    sku: str
    categoria_id: int
    existencias: int
    imagenes: tuple[ImagenAlmacenada, ...]
    estado: Estado
    creado_en: datetime
    actualizado_en: datetime
    eliminado_en: datetime | None = None

    @property
    def disponible(self) -> bool:
        return self.existencias > 0


@dataclass(frozen=True, slots=True)
class ProductoNuevo:
    nombre: str
    slug: str
    descripcion: str | None
    precio: Decimal
    sku: str
    categoria_id: int
    existencias: int
    imagenes: tuple[ImagenAlmacenada, ...]
    estado: Estado


@dataclass(frozen=True, slots=True)
class ProductoReemplazo:
    nombre: str
    slug: str
    descripcion: str | None
    precio: Decimal
    categoria_id: int
    existencias: int
    imagenes: tuple[ImagenAlmacenada, ...]
    estado: Estado


@dataclass(frozen=True, slots=True)
class ProductoConsulta:
    categoria_id: int | None = None
    producto_ids: frozenset[int] | None = None
    nombre: str | None = None
    disponible: bool | None = None
    estado: EstadoFiltro = EstadoFiltro.ACTIVO
    orden: OrdenProducto = OrdenProducto.RECIENTE


def _fecha(dia: int, hora: int) -> datetime:
    return datetime(2026, 11, dia, hora, 0, tzinfo=timezone.utc)


def _imagen(
    url: str,
    texto_alternativo: str | None = None,
    orden: int = 1,
    es_principal: bool = True,
) -> ImagenAlmacenada:
    return ImagenAlmacenada(url, texto_alternativo, orden, es_principal)


def _productos_iniciales() -> tuple[ProductoAlmacenado, ...]:
    return (
        ProductoAlmacenado(
            id=1,
            nombre="Tote Bag Aurora",
            slug="tote-bag-aurora",
            descripcion="Tote bag de lona con asas reforzadas.",
            precio=Decimal("899.00"),
            sku="BAG-TOT-001",
            categoria_id=2,
            existencias=12,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
                    "Tote Bag Aurora",
                    1,
                    True,
                ),
                _imagen(
                    "https://cdn.bagstore.com/productos/tote-aurora-2.jpg",
                    "Tote Bag Aurora vista lateral",
                    2,
                    False,
                ),
            ),
            estado=Estado.ACTIVO,
            creado_en=_fecha(1, 10),
            actualizado_en=_fecha(1, 10),
        ),
        ProductoAlmacenado(
            id=2,
            nombre="Tote Bag Oliva",
            slug="tote-bag-oliva",
            descripcion="Tote bag de lona en tono oliva.",
            precio=Decimal("749.00"),
            sku="BAG-TOT-002",
            categoria_id=2,
            existencias=0,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/tote-oliva-1.jpg",
                    "Tote Bag Oliva",
                ),
            ),
            estado=Estado.ACTIVO,
            creado_en=_fecha(1, 11),
            actualizado_en=_fecha(1, 11),
        ),
        ProductoAlmacenado(
            id=3,
            nombre="Cross Body Luna",
            slug="cross-body-luna",
            descripcion="Bolsa cross body con correa ajustable.",
            precio=Decimal("1099.00"),
            sku="BAG-CRO-001",
            categoria_id=1,
            existencias=5,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/cross-luna-1.jpg",
                    "Cross Body Luna",
                ),
            ),
            estado=Estado.ACTIVO,
            creado_en=_fecha(2, 9),
            actualizado_en=_fecha(2, 9),
        ),
        ProductoAlmacenado(
            id=4,
            nombre="Cross Body Noche",
            slug="cross-body-noche",
            descripcion="Bolsa cross body de edición nocturna.",
            precio=Decimal("1199.00"),
            sku="BAG-CRO-002",
            categoria_id=1,
            existencias=3,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/cross-noche-1.jpg",
                    "Cross Body Noche",
                ),
            ),
            estado=Estado.INACTIVO,
            creado_en=_fecha(2, 10),
            actualizado_en=_fecha(2, 10),
        ),
        ProductoAlmacenado(
            id=5,
            nombre="Mini Bag Sol",
            slug="mini-bag-sol",
            descripcion="Mini bag compacta para uso diario.",
            precio=Decimal("599.00"),
            sku="BAG-MIN-001",
            categoria_id=3,
            existencias=2,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/mini-sol-1.jpg",
                    "Mini Bag Sol",
                ),
            ),
            estado=Estado.ACTIVO,
            creado_en=_fecha(2, 11),
            actualizado_en=_fecha(2, 11),
        ),
        ProductoAlmacenado(
            id=6,
            nombre="Mini Bag Coral",
            slug="mini-bag-coral",
            descripcion="Mini bag agotada de temporada.",
            precio=Decimal("649.00"),
            sku="BAG-MIN-002",
            categoria_id=3,
            existencias=0,
            imagenes=(),
            estado=Estado.ACTIVO,
            creado_en=_fecha(3, 9),
            actualizado_en=_fecha(3, 9),
        ),
        ProductoAlmacenado(
            id=7,
            nombre="Tote Bag Arena",
            slug="tote-bag-arena",
            descripcion="Tote bag amplia en tono arena.",
            precio=Decimal("799.00"),
            sku="BAG-TOT-003",
            categoria_id=2,
            existencias=25,
            imagenes=(),
            estado=Estado.ACTIVO,
            creado_en=_fecha(3, 10),
            actualizado_en=_fecha(3, 10),
        ),
        ProductoAlmacenado(
            id=8,
            nombre="Cross Body Río",
            slug="cross-body-rio",
            descripcion="Cross body ligera con acabado texturizado.",
            precio=Decimal("949.00"),
            sku="BAG-CRO-003",
            categoria_id=1,
            existencias=8,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/cross-rio-1.jpg",
                    "Cross Body Río",
                ),
            ),
            estado=Estado.ACTIVO,
            creado_en=_fecha(3, 11),
            actualizado_en=_fecha(3, 11),
        ),
        ProductoAlmacenado(
            id=9,
            nombre="Mini Bag Perla",
            slug="mini-bag-perla",
            descripcion="Mini bag de edición limitada.",
            precio=Decimal("699.00"),
            sku="BAG-MIN-003",
            categoria_id=3,
            existencias=0,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/mini-perla-1.jpg",
                    "Mini Bag Perla",
                ),
            ),
            estado=Estado.INACTIVO,
            creado_en=_fecha(3, 12),
            actualizado_en=_fecha(3, 12),
        ),
        ProductoAlmacenado(
            id=10,
            nombre="Tote Bag Cielo",
            slug="tote-bag-cielo",
            descripcion="Tote bag de lona en tono cielo.",
            precio=Decimal("849.00"),
            sku="BAG-TOT-004",
            categoria_id=2,
            existencias=1,
            imagenes=(
                _imagen(
                    "https://cdn.bagstore.com/productos/tote-cielo-1.jpg",
                    "Tote Bag Cielo",
                ),
            ),
            estado=Estado.ACTIVO,
            creado_en=_fecha(3, 13),
            actualizado_en=_fecha(3, 13),
        ),
    )


def _normalizar_texto(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor.casefold())
    return "".join(
        caracter for caracter in normalizado if not unicodedata.combining(caracter)
    )


class ProductoRepositorioMemoria:
    def __init__(
        self,
        productos: tuple[ProductoAlmacenado, ...] | None = None,
    ) -> None:
        datos = productos if productos is not None else _productos_iniciales()
        self._productos = {producto.id: producto for producto in datos}
        self._siguiente_id = max((producto.id for producto in datos), default=0) + 1

    def listar(self, consulta: ProductoConsulta) -> list[ProductoAlmacenado]:
        productos = [
            producto
            for producto in self._productos.values()
            if producto.eliminado_en is None
        ]

        if consulta.estado == EstadoFiltro.ACTIVO:
            productos = [
                producto
                for producto in productos
                if producto.estado == Estado.ACTIVO
            ]
        elif consulta.estado == EstadoFiltro.INACTIVO:
            productos = [
                producto
                for producto in productos
                if producto.estado == Estado.INACTIVO
            ]

        if consulta.categoria_id is not None:
            productos = [
                producto
                for producto in productos
                if producto.categoria_id == consulta.categoria_id
            ]

        if consulta.producto_ids is not None:
            productos = [
                producto
                for producto in productos
                if producto.id in consulta.producto_ids
            ]

        if consulta.nombre:
            termino = _normalizar_texto(consulta.nombre)
            if termino:
                productos = [
                    producto
                    for producto in productos
                    if termino in _normalizar_texto(producto.nombre)
                ]

        if consulta.disponible is not None:
            productos = [
                producto
                for producto in productos
                if producto.disponible == consulta.disponible
            ]

        return self._ordenar(productos, consulta.orden)

    def obtener_por_id(self, producto_id: int) -> ProductoAlmacenado | None:
        producto = self._productos.get(producto_id)
        if producto is None or producto.eliminado_en is not None:
            return None
        return producto

    def crear(self, datos: ProductoNuevo) -> ProductoAlmacenado:
        ahora = datetime.now(timezone.utc)
        producto = ProductoAlmacenado(
            id=self._siguiente_id,
            nombre=datos.nombre,
            slug=datos.slug,
            descripcion=datos.descripcion,
            precio=datos.precio,
            sku=datos.sku,
            categoria_id=datos.categoria_id,
            existencias=datos.existencias,
            imagenes=datos.imagenes,
            estado=datos.estado,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        self._productos[producto.id] = producto
        self._siguiente_id += 1
        return producto

    def reemplazar(
        self, producto_id: int, datos: ProductoReemplazo
    ) -> ProductoAlmacenado:
        actual = self.obtener_por_id(producto_id)
        if actual is None:
            raise KeyError(producto_id)
        actualizado = replace(
            actual,
            nombre=datos.nombre,
            slug=datos.slug,
            descripcion=datos.descripcion,
            precio=datos.precio,
            categoria_id=datos.categoria_id,
            existencias=datos.existencias,
            imagenes=datos.imagenes,
            estado=datos.estado,
            actualizado_en=datetime.now(timezone.utc),
        )
        self._productos[producto_id] = actualizado
        return actualizado

    def eliminar_logico(self, producto_id: int) -> bool:
        actual = self.obtener_por_id(producto_id)
        if actual is None:
            return False
        ahora = datetime.now(timezone.utc)
        self._productos[producto_id] = replace(
            actual,
            eliminado_en=ahora,
            actualizado_en=ahora,
        )
        return True

    def existe_sku(self, sku: str, excluir_id: int | None = None) -> bool:
        objetivo = sku.strip().upper()
        return any(
            producto.sku == objetivo and producto.id != excluir_id
            for producto in self._productos.values()
        )

    def existe_slug(self, slug: str, excluir_id: int | None = None) -> bool:
        objetivo = slug.strip().lower()
        return any(
            producto.slug == objetivo and producto.id != excluir_id
            for producto in self._productos.values()
        )

    def contar_por_categoria(
        self,
        categoria_id: int,
        *,
        solo_activos: bool = False,
        incluir_eliminados: bool = False,
    ) -> int:
        total = 0
        for producto in self._productos.values():
            if producto.categoria_id != categoria_id:
                continue
            if not incluir_eliminados and producto.eliminado_en is not None:
                continue
            if solo_activos and producto.estado != Estado.ACTIVO:
                continue
            total += 1
        return total

    def existe_categoria_con_productos(
        self,
        categoria_id: int,
        *,
        incluir_eliminados: bool = True,
    ) -> bool:
        return any(
            producto.categoria_id == categoria_id
            and (incluir_eliminados or producto.eliminado_en is None)
            for producto in self._productos.values()
        )

    def contar_por_ids(
        self,
        producto_ids: Iterable[int],
        *,
        solo_activos: bool = False,
        incluir_eliminados: bool = False,
    ) -> int:
        total = 0
        for producto_id in set(producto_ids):
            producto = self._productos.get(producto_id)
            if producto is None:
                continue
            if not incluir_eliminados and producto.eliminado_en is not None:
                continue
            if solo_activos and producto.estado != Estado.ACTIVO:
                continue
            total += 1
        return total

    def ids_inexistentes(self, producto_ids: Iterable[int]) -> list[int]:
        return sorted(
            {
                producto_id
                for producto_id in producto_ids
                if self.obtener_por_id(producto_id) is None
            }
        )

    def _ordenar(
        self,
        productos: list[ProductoAlmacenado],
        orden: OrdenProducto,
    ) -> list[ProductoAlmacenado]:
        if orden == OrdenProducto.RECIENTE:
            return sorted(
                productos,
                key=lambda producto: (producto.creado_en, producto.id),
                reverse=True,
            )
        if orden == OrdenProducto.NOMBRE_ASC:
            return sorted(
                productos,
                key=lambda producto: (
                    _normalizar_texto(producto.nombre),
                    producto.id,
                ),
            )
        if orden == OrdenProducto.NOMBRE_DESC:
            return sorted(
                productos,
                key=lambda producto: (
                    _normalizar_texto(producto.nombre),
                    producto.id,
                ),
                reverse=True,
            )
        if orden == OrdenProducto.PRECIO_ASC:
            return sorted(
                productos,
                key=lambda producto: (producto.precio, producto.id),
            )
        return sorted(
            productos,
            key=lambda producto: (producto.precio, producto.id),
            reverse=True,
        )
