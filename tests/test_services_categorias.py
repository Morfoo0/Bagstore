import pytest

from app.core.errors import AppError
from app.repositories.categorias import CategoriaRepositorioMemoria
from app.repositories.productos import ProductoRepositorioMemoria
from app.schemas.categoria import (
    CategoriaCreate,
    CategoriaFiltros,
    CategoriaUpdate,
)
from app.schemas.errors import CodigoError
from app.services.categorias import CategoriaService


def crear_service(
    productos: ProductoRepositorioMemoria | None = None,
) -> CategoriaService:
    return CategoriaService(
        CategoriaRepositorioMemoria(),
        productos or ProductoRepositorioMemoria(),
    )


def test_listar_categorias_publicas_con_conteos() -> None:
    service = crear_service()

    resultado = service.listar(CategoriaFiltros())

    assert [categoria.id for categoria in resultado.datos] == [2, 1, 3]
    assert [categoria.total_productos for categoria in resultado.datos] == [
        4,
        2,
        2,
    ]
    assert resultado.paginacion.total == 3
    assert resultado.paginacion.total_paginas == 1


def test_listar_categorias_inactivas_requiere_admin() -> None:
    service = crear_service()
    service.crear(
        CategoriaCreate.model_validate(
            {"nombre": "Archivada", "estado": "inactivo"}
        )
    )
    filtros = CategoriaFiltros.model_validate({"estado": "inactivo"})

    with pytest.raises(AppError) as error:
        service.listar(filtros)

    assert error.value.status_code == 403
    assert error.value.codigo == CodigoError.ACCESO_DENEGADO

    resultado = service.listar(filtros, es_administrador=True)
    assert [categoria.slug for categoria in resultado.datos] == ["archivada"]


def test_obtener_categoria_inactiva_es_404_publico_y_200_admin() -> None:
    service = crear_service()
    creada = service.crear(
        CategoriaCreate.model_validate(
            {"nombre": "Archivada", "estado": "inactivo"}
        )
    )

    with pytest.raises(AppError) as error:
        service.obtener(creada.id)

    assert error.value.status_code == 404

    categoria = service.obtener(creada.id, es_administrador=True)
    assert categoria.estado.value == "inactivo"


def test_crear_categoria_genera_slug_y_valida_unicidad() -> None:
    service = crear_service()

    creada = service.crear(
        CategoriaCreate.model_validate({"nombre": "Bandoleras"})
    )
    assert creada.id == 4
    assert creada.slug == "bandoleras"
    assert creada.total_productos == 0

    with pytest.raises(AppError) as error:
        service.crear(
            CategoriaCreate.model_validate({"nombre": "Tote Bags"})
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "nombre"

    with pytest.raises(AppError) as error:
        service.crear(
            CategoriaCreate.model_validate(
                {"nombre": "Otra Tote", "slug": "tote-bags"}
            )
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "slug"


def test_crear_categoria_con_slug_generado_en_colision() -> None:
    service = crear_service()

    creada = service.crear(
        CategoriaCreate.model_validate({"nombre": "Tote Bags!"})
    )

    assert creada.slug == "tote-bags-2"


def test_actualizar_categoria_preserva_slug_y_defaults() -> None:
    service = crear_service()

    categoria = service.actualizar(
        1,
        CategoriaUpdate.model_validate(
            {"nombre": "Cross Body Premium", "estado": "activo"}
        ),
    )

    assert categoria.id == 1
    assert categoria.nombre == "Cross Body Premium"
    assert categoria.slug == "cross-body"
    assert categoria.descripcion is None
    assert categoria.orden == 0
    assert categoria.total_productos == 3


def test_actualizar_categoria_rechaza_nombre_y_slug_duplicados() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.actualizar(
            1,
            CategoriaUpdate.model_validate(
                {"nombre": "Tote Bags", "estado": "activo"}
            ),
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "nombre"

    with pytest.raises(AppError) as error:
        service.actualizar(
            1,
            CategoriaUpdate.model_validate(
                {
                    "nombre": "Cross Body",
                    "slug": "tote-bags",
                    "estado": "activo",
                }
            ),
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "slug"


def test_desactivar_categoria_con_productos_activos_devuelve_409() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.actualizar(
            2,
            CategoriaUpdate.model_validate(
                {"nombre": "Tote Bags", "estado": "inactivo"}
            ),
        )

    assert error.value.status_code == 409
    assert error.value.codigo == CodigoError.CONFLICTO_DEPENDENCIAS


def test_desactivar_categoria_vacia_es_permitido() -> None:
    service = crear_service()
    creada = service.crear(
        CategoriaCreate.model_validate({"nombre": "Vacía"})
    )

    categoria = service.actualizar(
        creada.id,
        CategoriaUpdate.model_validate(
            {"nombre": "Vacía", "estado": "inactivo"}
        ),
    )

    assert categoria.estado.value == "inactivo"


def test_eliminar_categoria_con_productos_devuelve_409() -> None:
    service = crear_service()

    with pytest.raises(AppError) as error:
        service.eliminar(2)

    assert error.value.status_code == 409
    assert error.value.codigo == CodigoError.CONFLICTO_DEPENDENCIAS


def test_eliminar_categoria_vacia_y_segundo_delete_404() -> None:
    service = crear_service()
    creada = service.crear(
        CategoriaCreate.model_validate({"nombre": "Temporal"})
    )

    service.eliminar(creada.id)

    with pytest.raises(AppError) as error:
        service.obtener(creada.id)

    assert error.value.status_code == 404

    with pytest.raises(AppError) as error:
        service.eliminar(creada.id)

    assert error.value.status_code == 404


def test_categoria_con_producto_eliminado_no_se_puede_eliminar() -> None:
    productos = ProductoRepositorioMemoria()
    service = CategoriaService(CategoriaRepositorioMemoria(), productos)
    assert productos.eliminar_logico(1) is True

    with pytest.raises(AppError) as error:
        service.eliminar(2)

    assert error.value.status_code == 409
    assert error.value.codigo == CodigoError.CONFLICTO_DEPENDENCIAS


def test_conteos_publico_y_admin_excluyen_eliminados() -> None:
    productos = ProductoRepositorioMemoria()
    service = CategoriaService(CategoriaRepositorioMemoria(), productos)

    publico = service.obtener(1)
    admin = service.obtener(1, es_administrador=True)
    assert publico.total_productos == 2
    assert admin.total_productos == 3

    assert productos.eliminar_logico(3) is True
    despues = service.obtener(1, es_administrador=True)
    assert despues.total_productos == 2


def test_listar_todos_para_admin_incluye_inactivas() -> None:
    service = crear_service()
    service.crear(
        CategoriaCreate.model_validate(
            {"nombre": "Archivada", "estado": "inactivo"}
        )
    )
    filtros = CategoriaFiltros.model_validate({"estado": "todos"})

    resultado = service.listar(filtros, es_administrador=True)

    assert resultado.paginacion.total == 4
