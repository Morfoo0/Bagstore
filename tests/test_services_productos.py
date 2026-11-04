from decimal import Decimal

import pytest

from app.core.errors import AppError
from app.repositories.categorias import (
    CategoriaAlmacenada,
    CategoriaRepositorioMemoria,
)
from app.repositories.colecciones import ColeccionRepositorioMemoria
from app.repositories.productos import ProductoRepositorioMemoria
from app.schemas.common import Estado
from app.schemas.errors import CodigoError
from app.schemas.producto import ProductoCreate, ProductoFiltros, ProductoUpdate
from app.services.productos import ProductoService


def crear_service(
    categorias: tuple[CategoriaAlmacenada, ...] | None = None,
) -> ProductoService:
    return ProductoService(
        ProductoRepositorioMemoria(),
        CategoriaRepositorioMemoria(categorias),
        ColeccionRepositorioMemoria(),
    )


def datos_producto(**overrides) -> dict:
    datos = {
        "nombre": "Tote Nueva",
        "precio": "123.45",
        "sku": "BAG-NEW-001",
        "categoria_id": 2,
        "existencias": 4,
    }
    datos.update(overrides)
    return datos


def datos_actualizacion(**overrides) -> dict:
    datos = {
        "nombre": "Tote Bag Aurora",
        "precio": "950.00",
        "categoria_id": 2,
        "existencias": 0,
        "imagenes": [],
        "estado": "activo",
    }
    datos.update(overrides)
    return datos


def test_crear_genera_slug_y_calcula_disponible() -> None:
    service = crear_service()

    producto = service.crear(
        ProductoCreate.model_validate(datos_producto())
    )

    assert producto.id == 11
    assert producto.slug == "tote-nueva"
    assert producto.disponible is True
    assert producto.colecciones == []


def test_crear_rechaza_categoria_inexistente() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.crear(
            ProductoCreate.model_validate(datos_producto(categoria_id=999))
        )

    assert error.value.status_code == 422
    assert error.value.codigo == CodigoError.VALIDACION_FALLIDA
    assert error.value.detalles[0].campo == "categoria_id"


def test_crear_rechaza_categoria_inactiva_para_producto_activo() -> None:
    categorias = (
        CategoriaAlmacenada(99, "Archivo", "archivo", Estado.INACTIVO),
    )
    service = crear_service(categorias)

    with pytest.raises(AppError) as error:
        service.crear(
            ProductoCreate.model_validate(
                datos_producto(categoria_id=99)
            )
        )

    assert error.value.status_code == 422

    inactivo = service.crear(
        ProductoCreate.model_validate(
            datos_producto(
                categoria_id=99,
                sku="BAG-ARC-001",
                estado="inactivo",
            )
        )
    )
    assert inactivo.estado == Estado.INACTIVO


def test_crear_rechaza_sku_duplicado() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.crear(
            ProductoCreate.model_validate(
                datos_producto(sku="BAG-TOT-001")
            )
        )

    assert error.value.status_code == 409
    assert error.value.codigo == CodigoError.CONFLICTO_UNICIDAD
    assert error.value.detalles[0].campo == "sku"


def test_crear_rechaza_slug_duplicado() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.crear(
            ProductoCreate.model_validate(
                datos_producto(slug="tote-bag-aurora")
            )
        )

    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "slug"


def test_crear_genera_slug_con_sufijo_si_hay_colision() -> None:
    service = crear_service()

    primero = service.crear(
        ProductoCreate.model_validate(
            datos_producto(nombre="Tote Bag Aurora")
        )
    )
    segundo = service.crear(
        ProductoCreate.model_validate(
            datos_producto(
                nombre="Tote Bag Aurora",
                sku="BAG-NEW-002",
            )
        )
    )

    assert primero.slug == "tote-bag-aurora-2"
    assert segundo.slug == "tote-bag-aurora-3"


def test_crear_rechaza_slug_no_generable() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.crear(
            ProductoCreate.model_validate(
                datos_producto(nombre="!!")
            )
        )

    assert error.value.status_code == 422
    assert error.value.detalles[0].campo == "slug"


def test_actualizar_rechaza_cambio_de_sku() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.actualizar(
            1,
            ProductoUpdate.model_validate(
                datos_actualizacion(sku="BAG-TOT-999")
            ),
        )

    assert error.value.status_code == 422
    assert error.value.detalles[0].campo == "sku"


def test_actualizar_preserva_slug_y_reemplaza_campos() -> None:
    service = crear_service()

    producto = service.actualizar(
        1,
        ProductoUpdate.model_validate(datos_actualizacion()),
    )

    assert producto.slug == "tote-bag-aurora"
    assert producto.descripcion is None
    assert producto.imagenes == []
    assert producto.existencias == 0
    assert producto.disponible is False
    assert [coleccion.slug for coleccion in producto.colecciones] == [
        "la-coleccion"
    ]


def test_actualizar_rechaza_slug_duplicado() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.actualizar(
            1,
            ProductoUpdate.model_validate(
                datos_actualizacion(slug="tote-bag-oliva")
            ),
        )

    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "slug"


def test_actualizar_permite_conservar_el_mismo_slug() -> None:
    service = crear_service()

    producto = service.actualizar(
        1,
        ProductoUpdate.model_validate(
            datos_actualizacion(slug="tote-bag-aurora")
        ),
    )

    assert producto.slug == "tote-bag-aurora"


def test_actualizar_producto_inexistente_devuelve_404() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.actualizar(
            999,
            ProductoUpdate.model_validate(datos_actualizacion()),
        )

    assert error.value.status_code == 404


def test_obtener_inactivo_es_404_publico_y_200_admin() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.obtener(4)

    assert error.value.status_code == 404

    producto = service.obtener(4, es_administrador=True)
    assert producto.estado == Estado.INACTIVO


def test_listar_inactivos_requiere_administrador() -> None:
    service = crear_service()
    filtros = ProductoFiltros.model_validate({"estado": "inactivo"})

    with pytest.raises(AppError) as error:
        service.listar(filtros)

    assert error.value.status_code == 403
    assert error.value.codigo == CodigoError.ACCESO_DENEGADO

    resultado = service.listar(filtros, es_administrador=True)
    assert resultado.paginacion.total == 2


def test_listar_rechaza_filtros_incompatibles() -> None:
    service = crear_service()
    filtros = ProductoFiltros.model_validate(
        {"categoria": "tote-bags", "categoria_id": 2}
    )

    with pytest.raises(AppError) as error:
        service.listar(filtros)

    assert error.value.status_code == 400
    assert error.value.codigo == CodigoError.SOLICITUD_INVALIDA


def test_listar_pagina_y_total_paginas() -> None:
    service = crear_service()
    filtros = ProductoFiltros.model_validate(
        {"pagina": 2, "por_pagina": 3}
    )

    resultado = service.listar(filtros)

    assert len(resultado.datos) == 3
    assert resultado.paginacion.total == 8
    assert resultado.paginacion.total_paginas == 3

    fuera_de_rango = service.listar(
        ProductoFiltros.model_validate(
            {"pagina": 4, "por_pagina": 3}
        )
    )
    assert fuera_de_rango.datos == []
    assert fuera_de_rango.paginacion.total == 8
    assert fuera_de_rango.paginacion.total_paginas == 3


def test_listar_filtra_por_coleccion_activa() -> None:
    service = crear_service()
    resultado = service.listar(
        ProductoFiltros.model_validate({"coleccion": "la-coleccion"})
    )

    assert {producto.id for producto in resultado.datos} == {1, 3, 6, 8}


def test_listar_coleccion_inactiva_solo_para_admin() -> None:
    service = crear_service()
    filtros = ProductoFiltros.model_validate({"coleccion": "archivo"})

    publico = service.listar(filtros)
    admin = service.listar(filtros, es_administrador=True)

    assert publico.paginacion.total == 0
    assert [producto.id for producto in admin.datos] == [2]


def test_listar_categoria_inexistente_devuelve_vacio() -> None:
    service = crear_service()
    resultado = service.listar(
        ProductoFiltros.model_validate({"categoria": "no-existe"})
    )

    assert resultado.datos == []
    assert resultado.paginacion.total == 0


def test_detalle_excluye_coleccion_inactiva_en_publico() -> None:
    service = crear_service()

    publico = service.obtener(2)
    admin = service.obtener(2, es_administrador=True)

    assert publico.colecciones == []
    assert [coleccion.slug for coleccion in admin.colecciones] == ["archivo"]


def test_eliminar_borra_logico_y_quita_relaciones() -> None:
    productos = ProductoRepositorioMemoria()
    colecciones = ColeccionRepositorioMemoria()
    service = ProductoService(
        productos,
        CategoriaRepositorioMemoria(),
        colecciones,
    )

    service.eliminar(1)

    assert productos.obtener_por_id(1) is None
    assert colecciones.listar_por_producto(1) == []
    assert productos.existe_sku("BAG-TOT-001") is True
    assert productos.existe_slug("tote-bag-aurora") is True

    with pytest.raises(AppError) as error:
        service.eliminar(1)

    assert error.value.status_code == 404


def test_crear_calcula_disponible_con_existencias_cero() -> None:
    service = crear_service()

    producto = service.crear(
        ProductoCreate.model_validate(
            datos_producto(
                precio=Decimal("10.00"),
                existencias=0,
            )
        )
    )

    assert producto.disponible is False
