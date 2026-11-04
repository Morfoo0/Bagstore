import pytest

from app.core.errors import AppError
from app.repositories.colecciones import ColeccionRepositorioMemoria
from app.repositories.productos import ProductoRepositorioMemoria
from app.schemas.coleccion import (
    ColeccionCreate,
    ColeccionFiltros,
    ColeccionUpdate,
)
from app.schemas.common import Estado
from app.schemas.errors import CodigoError
from app.services.colecciones import ColeccionService


def crear_service() -> tuple[
    ColeccionService,
    ColeccionRepositorioMemoria,
    ProductoRepositorioMemoria,
]:
    productos = ProductoRepositorioMemoria()
    colecciones = ColeccionRepositorioMemoria()
    return (
        ColeccionService(colecciones, productos),
        colecciones,
        productos,
    )


def test_listar_colecciones_publicas_y_admin() -> None:
    service, _, _ = crear_service()

    publico = service.listar(ColeccionFiltros())
    admin = service.listar(
        ColeccionFiltros.model_validate({"estado": "todos"}),
        es_administrador=True,
    )

    assert [coleccion.slug for coleccion in publico.datos] == ["la-coleccion"]
    assert publico.datos[0].total_productos == 4
    assert [coleccion.slug for coleccion in admin.datos] == [
        "la-coleccion",
        "archivo",
    ]
    assert [coleccion.total_productos for coleccion in admin.datos] == [4, 1]


def test_listar_colecciones_inactivas_requiere_admin() -> None:
    service, _, _ = crear_service()
    filtros = ColeccionFiltros.model_validate({"estado": "inactivo"})

    with pytest.raises(AppError) as error:
        service.listar(filtros)

    assert error.value.status_code == 403
    assert error.value.codigo == CodigoError.ACCESO_DENEGADO

    resultado = service.listar(filtros, es_administrador=True)
    assert [coleccion.slug for coleccion in resultado.datos] == ["archivo"]


def test_obtener_coleccion_inactiva_es_404_publico_y_200_admin() -> None:
    service, _, _ = crear_service()

    with pytest.raises(AppError) as error:
        service.obtener(2)

    assert error.value.status_code == 404

    coleccion = service.obtener(2, es_administrador=True)
    assert coleccion.estado.value == "inactivo"
    assert coleccion.total_productos == 1


def test_crear_coleccion_genera_slug_y_valida_unicidad() -> None:
    service, _, _ = crear_service()

    creada = service.crear(
        ColeccionCreate.model_validate({"nombre": "Verano"})
    )
    assert creada.id == 3
    assert creada.slug == "verano"
    assert creada.total_productos == 0

    with pytest.raises(AppError) as error:
        service.crear(
            ColeccionCreate.model_validate({"nombre": "La Colección"})
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "nombre"

    with pytest.raises(AppError) as error:
        service.crear(
            ColeccionCreate.model_validate(
                {"nombre": "Otra colección", "slug": "la-coleccion"}
            )
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "slug"


def test_crear_coleccion_con_slug_generado_en_colision() -> None:
    service, _, _ = crear_service()

    creada = service.crear(
        ColeccionCreate.model_validate({"nombre": "La Colección!"})
    )

    assert creada.slug == "la-coleccion-2"


def test_crear_coleccion_valida_producto_ids() -> None:
    service, _, productos = crear_service()

    with pytest.raises(AppError) as error:
        service.crear(
            ColeccionCreate.model_validate(
                {"nombre": "Inválida", "producto_ids": [999]}
            )
        )

    assert error.value.status_code == 422
    assert error.value.detalles[0].campo == "producto_ids"

    assert productos.eliminar_logico(1) is True
    with pytest.raises(AppError) as error:
        service.crear(
            ColeccionCreate.model_validate(
                {"nombre": "Con eliminado", "producto_ids": [1]}
            )
        )

    assert error.value.status_code == 422


def test_conteos_de_coleccion_publico_y_admin() -> None:
    service, _, _ = crear_service()
    creada = service.crear(
        ColeccionCreate.model_validate(
            {"nombre": "Mixta", "producto_ids": [1, 4]}
        )
    )

    publico = service.obtener(creada.id)
    admin = service.obtener(creada.id, es_administrador=True)

    assert publico.total_productos == 1
    assert admin.total_productos == 2


def test_actualizar_coleccion_reemplaza_membresia_y_defaults() -> None:
    service, colecciones, _ = crear_service()

    coleccion = service.actualizar(
        1,
        ColeccionUpdate.model_validate(
            {
                "nombre": "La Colección",
                "estado": "activo",
                "producto_ids": [1, 2],
            }
        ),
    )

    assert coleccion.slug == "la-coleccion"
    assert coleccion.descripcion is None
    assert coleccion.imagen_portada_url is None
    assert coleccion.total_productos == 2
    almacenada = colecciones.obtener_por_id(1)
    assert almacenada is not None
    assert almacenada.producto_ids == (1, 2)


def test_actualizar_coleccion_permite_vaciar_membresia() -> None:
    service, colecciones, _ = crear_service()

    coleccion = service.actualizar(
        1,
        ColeccionUpdate.model_validate(
            {
                "nombre": "La Colección",
                "estado": "activo",
                "producto_ids": [],
            }
        ),
    )

    assert coleccion.total_productos == 0
    almacenada = colecciones.obtener_por_id(1)
    assert almacenada is not None
    assert almacenada.producto_ids == ()


def test_desactivar_coleccion_no_modifica_productos() -> None:
    service, _, productos = crear_service()

    coleccion = service.actualizar(
        1,
        ColeccionUpdate.model_validate(
            {
                "nombre": "La Colección",
                "estado": "inactivo",
                "producto_ids": [1, 3, 6, 8],
            }
        ),
    )

    assert coleccion.estado == Estado.INACTIVO
    for producto_id in (1, 3, 6, 8):
        producto = productos.obtener_por_id(producto_id)
        assert producto is not None
        assert producto.estado == Estado.ACTIVO


def test_actualizar_coleccion_rechaza_nombre_y_slug_duplicados() -> None:
    service, _, _ = crear_service()

    with pytest.raises(AppError) as error:
        service.actualizar(
            1,
            ColeccionUpdate.model_validate(
                {
                    "nombre": "Archivo",
                    "estado": "activo",
                    "producto_ids": [],
                }
            ),
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "nombre"

    with pytest.raises(AppError) as error:
        service.actualizar(
            1,
            ColeccionUpdate.model_validate(
                {
                    "nombre": "La Colección",
                    "slug": "archivo",
                    "estado": "activo",
                    "producto_ids": [],
                }
            ),
        )
    assert error.value.status_code == 409
    assert error.value.detalles[0].campo == "slug"


def test_actualizar_coleccion_valida_producto_ids() -> None:
    service, _, productos = crear_service()
    assert productos.eliminar_logico(2) is True

    with pytest.raises(AppError) as error:
        service.actualizar(
            1,
            ColeccionUpdate.model_validate(
                {
                    "nombre": "La Colección",
                    "estado": "activo",
                    "producto_ids": [2],
                }
            ),
        )

    assert error.value.status_code == 422
    assert error.value.detalles[0].campo == "producto_ids"


def test_eliminar_coleccion_no_elimina_productos() -> None:
    service, colecciones, productos = crear_service()

    service.eliminar(1)

    assert colecciones.obtener_por_id(1) is None
    assert productos.obtener_por_id(1) is not None
    assert productos.obtener_por_id(3) is not None
    assert productos.obtener_por_id(6) is not None
    assert productos.obtener_por_id(8) is not None

    with pytest.raises(AppError) as error:
        service.eliminar(1)

    assert error.value.status_code == 404


def test_eliminar_coleccion_inexistente_devuelve_404() -> None:
    service, _, _ = crear_service()

    with pytest.raises(AppError) as error:
        service.eliminar(999)

    assert error.value.status_code == 404


def test_filtrar_colecciones_por_nombre() -> None:
    service, _, _ = crear_service()

    resultado = service.listar(
        ColeccionFiltros.model_validate({"nombre": "coleccion"})
    )

    assert [coleccion.id for coleccion in resultado.datos] == [1]
