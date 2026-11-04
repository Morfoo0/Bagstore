from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.repositories.productos import (
    ProductoConsulta,
    ProductoNuevo,
    ProductoReemplazo,
    ProductoRepositorioMemoria,
)
from app.schemas.common import Estado, EstadoFiltro
from app.schemas.producto import OrdenProducto


@pytest.fixture
def repositorio() -> ProductoRepositorioMemoria:
    return ProductoRepositorioMemoria()


def test_listar_solo_activos_por_defecto(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    productos = repositorio.listar(ProductoConsulta())

    assert [producto.id for producto in productos] == [10, 8, 7, 6, 5, 3, 2, 1]
    assert all(producto.estado == Estado.ACTIVO for producto in productos)


def test_listar_todos_e_inactivos(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    todos = repositorio.listar(
        ProductoConsulta(estado=EstadoFiltro.TODOS)
    )
    inactivos = repositorio.listar(
        ProductoConsulta(estado=EstadoFiltro.INACTIVO)
    )

    assert len(todos) == 10
    assert [producto.id for producto in inactivos] == [9, 4]


def test_filtrar_por_categoria_nombre_y_disponibilidad(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    productos = repositorio.listar(
        ProductoConsulta(
            categoria_id=2,
            nombre="oliva",
            disponible=False,
        )
    )

    assert [producto.id for producto in productos] == [2]


def test_busqueda_de_nombre_ignora_acentos(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    productos = repositorio.listar(ProductoConsulta(nombre="rio"))

    assert [producto.id for producto in productos] == [8]


def test_filtrar_por_ids_de_coleccion(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    productos = repositorio.listar(
        ProductoConsulta(producto_ids=frozenset({1, 3, 6}))
    )

    assert {producto.id for producto in productos} == {1, 3, 6}


@pytest.mark.parametrize(
    ("orden", "primero", "ultimo"),
    [
        (OrdenProducto.RECIENTE, 10, 1),
        (OrdenProducto.NOMBRE_ASC, 3, 2),
        (OrdenProducto.NOMBRE_DESC, 2, 3),
        (OrdenProducto.PRECIO_ASC, 5, 3),
        (OrdenProducto.PRECIO_DESC, 3, 5),
    ],
)
def test_ordenamientos(
    repositorio: ProductoRepositorioMemoria,
    orden: OrdenProducto,
    primero: int,
    ultimo: int,
) -> None:
    productos = repositorio.listar(ProductoConsulta(orden=orden))

    assert productos[0].id == primero
    assert productos[-1].id == ultimo


def test_crear_asigna_id_y_timestamps(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    producto = repositorio.crear(
        ProductoNuevo(
            nombre="Tote Nueva",
            slug="tote-nueva",
            descripcion=None,
            precio=Decimal("123.45"),
            sku="BAG-NEW-001",
            categoria_id=2,
            existencias=4,
            imagenes=(),
            estado=Estado.ACTIVO,
        )
    )

    assert producto.id == 11
    assert producto.creado_en.tzinfo is not None
    assert producto.actualizado_en == producto.creado_en
    assert repositorio.obtener_por_id(11) == producto


def test_eliminar_logico_reserva_sku_slug_e_id(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    assert repositorio.eliminar_logico(1) is True
    assert repositorio.obtener_por_id(1) is None
    assert repositorio.existe_sku("BAG-TOT-001") is True
    assert repositorio.existe_slug("tote-bag-aurora") is True
    assert repositorio.existe_sku("BAG-TOT-001", excluir_id=1) is False
    assert repositorio.eliminar_logico(1) is False

    nuevo = repositorio.crear(
        ProductoNuevo(
            nombre="Tote Nueva",
            slug="tote-nueva",
            descripcion=None,
            precio=Decimal("100.00"),
            sku="BAG-NEW-001",
            categoria_id=2,
            existencias=1,
            imagenes=(),
            estado=Estado.ACTIVO,
        )
    )

    assert nuevo.id == 11


def test_reemplazar_preserva_id_sku_y_creado_en(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    actual = repositorio.obtener_por_id(1)
    assert actual is not None

    reemplazado = repositorio.reemplazar(
        1,
        ProductoReemplazo(
            nombre="Tote Aurora Renovada",
            slug="tote-aurora-renovada",
            descripcion="Nueva descripción.",
            precio=Decimal("950.00"),
            categoria_id=2,
            existencias=0,
            imagenes=(),
            estado=Estado.INACTIVO,
        ),
    )

    assert reemplazado.id == actual.id
    assert reemplazado.sku == actual.sku
    assert reemplazado.creado_en == actual.creado_en
    assert reemplazado.nombre == "Tote Aurora Renovada"
    assert reemplazado.disponible is False
    assert reemplazado.actualizado_en >= actual.actualizado_en


def test_entidades_almacenadas_son_inmutables(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    producto = repositorio.obtener_por_id(1)
    assert producto is not None

    with pytest.raises(FrozenInstanceError):
        producto.nombre = "Cambio directo"


def test_fecha_de_creacion_es_utc(
    repositorio: ProductoRepositorioMemoria,
) -> None:
    producto = repositorio.obtener_por_id(1)
    assert producto is not None
    assert producto.creado_en.tzinfo is not None
    assert producto.creado_en.utcoffset().total_seconds() == 0
