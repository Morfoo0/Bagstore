from app.repositories.colecciones import (
    ColeccionConsulta,
    ColeccionNueva,
    ColeccionReemplazo,
    ColeccionRepositorioMemoria,
)
from app.schemas.common import Estado, EstadoFiltro


def test_listar_colecciones_ordenadas_por_id() -> None:
    repositorio = ColeccionRepositorioMemoria()

    colecciones = repositorio.listar()

    assert [coleccion.id for coleccion in colecciones] == [1, 2]
    assert colecciones[0].producto_ids == (1, 3, 6, 8)
    assert colecciones[1].estado == Estado.INACTIVO


def test_filtrar_colecciones_por_nombre_y_estado() -> None:
    repositorio = ColeccionRepositorioMemoria()

    por_nombre = repositorio.listar(ColeccionConsulta(nombre="coleccion"))
    inactivas = repositorio.listar(
        ColeccionConsulta(estado=EstadoFiltro.INACTIVO)
    )

    assert [coleccion.id for coleccion in por_nombre] == [1]
    assert [coleccion.id for coleccion in inactivas] == [2]


def test_crear_y_reemplazar_coleccion() -> None:
    repositorio = ColeccionRepositorioMemoria()

    creada = repositorio.crear(
        ColeccionNueva(
            nombre="Verano",
            slug="verano",
            descripcion="Selección de verano.",
            estado=Estado.ACTIVO,
            imagen_portada_url="https://cdn.bagstore.com/colecciones/verano.jpg",
            producto_ids=(1, 2),
        )
    )
    assert creada.id == 3
    assert creada.producto_ids == (1, 2)

    reemplazada = repositorio.reemplazar(
        3,
        ColeccionReemplazo(
            nombre="Verano 2027",
            slug="verano-2027",
            descripcion=None,
            estado=Estado.INACTIVO,
            imagen_portada_url=None,
            producto_ids=(4,),
        ),
    )

    assert reemplazada.id == creada.id
    assert reemplazada.creado_en == creada.creado_en
    assert reemplazada.nombre == "Verano 2027"
    assert reemplazada.descripcion is None
    assert reemplazada.imagen_portada_url is None
    assert reemplazada.producto_ids == (4,)
    assert repositorio.obtener_por_id(3) == reemplazada


def test_unicidad_de_nombre_y_slug() -> None:
    repositorio = ColeccionRepositorioMemoria()

    assert repositorio.existe_nombre("la colección") is True
    assert repositorio.existe_nombre("LA COLECCIÓN") is True
    assert repositorio.existe_nombre("la colección", excluir_id=1) is False
    assert repositorio.existe_slug("la-coleccion") is True
    assert repositorio.existe_slug("la-coleccion", excluir_id=1) is False
    assert repositorio.existe_slug("nueva-coleccion") is False


def test_listar_por_producto_y_eliminar_relacion() -> None:
    repositorio = ColeccionRepositorioMemoria()

    assert [coleccion.id for coleccion in repositorio.listar_por_producto(1)] == [1]
    assert [coleccion.id for coleccion in repositorio.listar_por_producto(2)] == [2]

    repositorio.eliminar_producto_de_todas(1)

    assert repositorio.listar_por_producto(1) == []
    coleccion = repositorio.obtener_por_id(1)
    assert coleccion is not None
    assert coleccion.producto_ids == (3, 6, 8)


def test_eliminar_coleccion_es_fisico() -> None:
    repositorio = ColeccionRepositorioMemoria()

    assert repositorio.eliminar(1) is True
    assert repositorio.obtener_por_id(1) is None
    assert repositorio.eliminar(1) is False
    assert [coleccion.id for coleccion in repositorio.listar()] == [2]
