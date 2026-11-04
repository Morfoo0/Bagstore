from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.categoria import (
    CategoriaCreate,
    CategoriaResumen,
    CategoriaResponse,
    CategoriaUpdate,
)
from app.schemas.coleccion import ColeccionCreate, ColeccionUpdate
from app.schemas.common import Estado, Paginacion
from app.schemas.producto import (
    OrdenProducto,
    ProductoCreate,
    ProductoFiltros,
    ProductoResumen,
    ProductoUpdate,
)


def datos_producto() -> dict:
    return {
        "nombre": "Tote Bag Aurora",
        "slug": "Tote Bag Aurora",
        "descripcion": "Tote bag de lona con asas reforzadas.",
        "precio": "899.00",
        "sku": "bag-tot-001",
        "categoria_id": 2,
        "existencias": 12,
        "imagenes": [
            {
                "url": "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
                "texto_alternativo": "Tote Bag Aurora",
            }
        ],
        "estado": "activo",
    }


def test_producto_create_normaliza_campos_y_asigna_imagen_principal() -> None:
    producto = ProductoCreate.model_validate(datos_producto())

    assert producto.nombre == "Tote Bag Aurora"
    assert producto.slug == "tote-bag-aurora"
    assert producto.sku == "BAG-TOT-001"
    assert producto.precio == Decimal("899.00")
    assert producto.estado == Estado.ACTIVO
    assert producto.imagenes[0].orden == 1
    assert producto.imagenes[0].es_principal is True


def test_producto_create_aplica_valores_por_defecto() -> None:
    datos = datos_producto()
    datos.pop("slug")
    datos.pop("estado")
    datos.pop("imagenes")

    producto = ProductoCreate.model_validate(datos)

    assert producto.slug is None
    assert producto.estado == Estado.ACTIVO
    assert producto.imagenes == []


@pytest.mark.parametrize(
    "precio",
    ["0", "-1", "1000000.00", "10.999", "Infinity"],
)
def test_producto_create_rechaza_precios_invalidos(precio: str) -> None:
    datos = datos_producto()
    datos["precio"] = precio

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


@pytest.mark.parametrize(
    "sku",
    ["AB", "BAG_TOT_001", "BAG TOT 001", "BAG--TOT"],
)
def test_producto_create_rechaza_skus_invalidos(sku: str) -> None:
    datos = datos_producto()
    datos["sku"] = sku

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


def test_producto_create_normaliza_sku_minusculas() -> None:
    datos = datos_producto()
    datos["sku"] = "bag-tot-001"

    producto = ProductoCreate.model_validate(datos)

    assert producto.sku == "BAG-TOT-001"


@pytest.mark.parametrize("existencias", [-1, 1_000_001])
def test_producto_create_rechaza_existencias_invalidas(
    existencias: int,
) -> None:
    datos = datos_producto()
    datos["existencias"] = existencias

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


def test_producto_create_rechaza_campos_desconocidos() -> None:
    datos = datos_producto()
    datos["campo_extra"] = "no permitido"

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


def test_producto_create_rechaza_mas_de_diez_imagenes() -> None:
    datos = datos_producto()
    datos["imagenes"] = [
        {"url": f"https://cdn.bagstore.com/productos/{indice}.jpg"}
        for indice in range(11)
    ]

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


def test_producto_create_rechaza_ordenes_duplicados() -> None:
    datos = datos_producto()
    datos["imagenes"] = [
        {
            "url": "https://cdn.bagstore.com/productos/1.jpg",
            "orden": 1,
        },
        {
            "url": "https://cdn.bagstore.com/productos/2.jpg",
            "orden": 1,
        },
    ]

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


def test_producto_create_rechaza_multiples_imagenes_principales() -> None:
    datos = datos_producto()
    datos["imagenes"] = [
        {
            "url": "https://cdn.bagstore.com/productos/1.jpg",
            "es_principal": True,
        },
        {
            "url": "https://cdn.bagstore.com/productos/2.jpg",
            "es_principal": True,
        },
    ]

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


@pytest.mark.parametrize(
    "url",
    ["ftp://cdn.bagstore.com/productos/1.jpg", "no-es-una-url"],
)
def test_producto_create_rechaza_urls_invalidas(url: str) -> None:
    datos = datos_producto()
    datos["imagenes"] = [{"url": url}]

    with pytest.raises(ValidationError):
        ProductoCreate.model_validate(datos)


def test_producto_update_exige_imagenes_y_estado() -> None:
    datos = datos_producto()
    datos.pop("imagenes")
    datos.pop("estado")

    with pytest.raises(ValidationError) as error:
        ProductoUpdate.model_validate(datos)

    campos = {item["loc"][0] for item in error.value.errors()}
    assert {"imagenes", "estado"} <= campos


def test_producto_update_permite_imagenes_vacias_y_sku_omitido() -> None:
    datos = datos_producto()
    datos["imagenes"] = []
    datos.pop("sku")
    datos.pop("slug")
    datos.pop("descripcion")

    producto = ProductoUpdate.model_validate(datos)

    assert producto.imagenes == []
    assert producto.sku is None
    assert producto.slug is None
    assert producto.descripcion is None


def test_categoria_create_normaliza_slug_y_estado_por_defecto() -> None:
    categoria = CategoriaCreate.model_validate(
        {
            "nombre": "  Cross Body  ",
            "slug": "Cross Body",
            "descripcion": "Bolsas cross body.",
            "orden": 2,
        }
    )

    assert categoria.nombre == "Cross Body"
    assert categoria.slug == "cross-body"
    assert categoria.estado == Estado.ACTIVO


def test_categoria_update_exige_estado_y_aplica_defaults() -> None:
    with pytest.raises(ValidationError):
        CategoriaUpdate.model_validate({"nombre": "Cross Body"})

    categoria = CategoriaUpdate.model_validate(
        {"nombre": "Cross Body", "estado": "inactivo"}
    )

    assert categoria.slug is None
    assert categoria.descripcion is None
    assert categoria.orden == 0
    assert categoria.estado == Estado.INACTIVO


def test_coleccion_create_normaliza_slug_y_url() -> None:
    coleccion = ColeccionCreate.model_validate(
        {
            "nombre": "La Colección",
            "slug": "La Colección",
            "imagen_portada_url": "https://cdn.bagstore.com/colecciones/la-coleccion.jpg",
            "producto_ids": [12, 18],
        }
    )

    assert coleccion.slug == "la-coleccion"
    assert coleccion.estado == Estado.ACTIVO
    assert coleccion.producto_ids == [12, 18]


def test_coleccion_create_producto_ids_es_opcional() -> None:
    coleccion = ColeccionCreate.model_validate({"nombre": "La Colección"})

    assert coleccion.producto_ids is None


def test_coleccion_update_exige_estado_y_producto_ids() -> None:
    with pytest.raises(ValidationError) as error:
        ColeccionUpdate.model_validate({"nombre": "La Colección"})

    campos = {item["loc"][0] for item in error.value.errors()}
    assert {"estado", "producto_ids"} <= campos


def test_coleccion_update_permite_lista_vacia() -> None:
    coleccion = ColeccionUpdate.model_validate(
        {
            "nombre": "La Colección",
            "estado": "activo",
            "producto_ids": [],
        }
    )

    assert coleccion.producto_ids == []


def test_coleccion_rechaza_productos_duplicados() -> None:
    with pytest.raises(ValidationError):
        ColeccionCreate.model_validate(
            {"nombre": "La Colección", "producto_ids": [12, 12]}
        )


def test_coleccion_rechaza_mas_de_doscientos_productos() -> None:
    with pytest.raises(ValidationError):
        ColeccionCreate.model_validate(
            {"nombre": "La Colección", "producto_ids": list(range(1, 202))}
        )


def test_coleccion_rechaza_url_invalida() -> None:
    with pytest.raises(ValidationError):
        ColeccionCreate.model_validate(
            {
                "nombre": "La Colección",
                "imagen_portada_url": "ftp://cdn.bagstore.com/portada.jpg",
            }
        )


def test_paginacion_valida_limites() -> None:
    paginacion = Paginacion(
        pagina=1, por_pagina=20, total=1, total_paginas=1
    )

    assert paginacion.pagina == 1

    with pytest.raises(ValidationError):
        Paginacion(pagina=0, por_pagina=20, total=1, total_paginas=1)

    with pytest.raises(ValidationError):
        Paginacion(pagina=1, por_pagina=101, total=1, total_paginas=1)


def test_filtros_producto_aplican_defaults_y_normalizan_slug() -> None:
    filtros = ProductoFiltros.model_validate({"categoria": "Tote Bags"})

    assert filtros.categoria == "tote-bags"
    assert filtros.estado == Estado.ACTIVO
    assert filtros.pagina == 1
    assert filtros.por_pagina == 20
    assert filtros.orden == OrdenProducto.RECIENTE


def test_filtros_producto_rechazan_combinaciones_incompatibles() -> None:
    filtros = ProductoFiltros.model_validate(
        {"categoria": "tote-bags", "categoria_id": 2}
    )

    with pytest.raises(ValueError):
        filtros.validar_combinaciones()


def test_respuesta_serializa_precio_como_numero_y_fecha_con_z() -> None:
    categoria = CategoriaResponse(
        id=2,
        nombre="Tote Bags",
        slug="tote-bags",
        descripcion="Bolsas tote.",
        estado=Estado.ACTIVO,
        orden=1,
        total_productos=8,
        creado_en=datetime(2026, 11, 3, 18, 0, tzinfo=timezone.utc),
        actualizado_en=datetime(2026, 11, 3, 18, 0, tzinfo=timezone.utc),
    )
    resumen = ProductoResumen(
        id=12,
        nombre="Tote Bag Aurora",
        slug="tote-bag-aurora",
        precio=Decimal("899.00"),
        disponible=True,
        estado=Estado.ACTIVO,
        imagen_principal=None,
        categoria=CategoriaResumen(
            id=2, nombre="Tote Bags", slug="tote-bags"
        ),
    )

    datos_categoria = categoria.model_dump(mode="json")
    datos_resumen = resumen.model_dump(mode="json")

    assert datos_categoria["creado_en"] == "2026-11-03T18:00:00Z"
    assert datos_resumen["precio"] == 899.0
    assert isinstance(datos_resumen["precio"], float)
