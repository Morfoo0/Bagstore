from app.repositories.categorias import (
    CategoriaConsulta,
    CategoriaNueva,
    CategoriaReemplazo,
    CategoriaRepositorioMemoria,
)
from app.schemas.common import Estado, EstadoFiltro


def test_listar_categorias_ordenadas_por_orden() -> None:
    repositorio = CategoriaRepositorioMemoria()

    categorias = repositorio.listar()

    assert [categoria.id for categoria in categorias] == [2, 1, 3]
    assert [categoria.nombre for categoria in categorias] == [
        "Tote Bags",
        "Cross Body",
        "Mini Bags",
    ]


def test_filtrar_categorias_por_nombre_y_estado() -> None:
    repositorio = CategoriaRepositorioMemoria()

    por_nombre = repositorio.listar(CategoriaConsulta(nombre="tote"))
    assert [categoria.id for categoria in por_nombre] == [2]

    repositorio.crear(
        CategoriaNueva(
            nombre="Archivada",
            slug="archivada",
            descripcion=None,
            estado=Estado.INACTIVO,
            orden=9,
        )
    )
    inactivas = repositorio.listar(
        CategoriaConsulta(estado=EstadoFiltro.INACTIVO)
    )
    assert [categoria.slug for categoria in inactivas] == ["archivada"]


def test_crear_y_reemplazar_categoria() -> None:
    repositorio = CategoriaRepositorioMemoria()

    creada = repositorio.crear(
        CategoriaNueva(
            nombre="Bandoleras",
            slug="bandoleras",
            descripcion="Bolsas bandolera.",
            estado=Estado.ACTIVO,
            orden=4,
        )
    )
    assert creada.id == 4
    assert creada.creado_en.tzinfo is not None

    reemplazada = repositorio.reemplazar(
        4,
        CategoriaReemplazo(
            nombre="Bandoleras Premium",
            slug="bandoleras-premium",
            descripcion=None,
            estado=Estado.INACTIVO,
            orden=0,
        ),
    )

    assert reemplazada.id == creada.id
    assert reemplazada.creado_en == creada.creado_en
    assert reemplazada.nombre == "Bandoleras Premium"
    assert reemplazada.slug == "bandoleras-premium"
    assert reemplazada.descripcion is None
    assert reemplazada.estado == Estado.INACTIVO
    assert repositorio.obtener_por_id(4) == reemplazada


def test_unicidad_de_nombre_y_slug() -> None:
    repositorio = CategoriaRepositorioMemoria()

    assert repositorio.existe_nombre("tote bags") is True
    assert repositorio.existe_nombre("TOTE BAGS") is True
    assert repositorio.existe_nombre("tote bags", excluir_id=2) is False
    assert repositorio.existe_slug("tote-bags") is True
    assert repositorio.existe_slug("tote-bags", excluir_id=2) is False
    assert repositorio.existe_slug("nueva-categoria") is False


def test_eliminar_categoria_es_fisico() -> None:
    repositorio = CategoriaRepositorioMemoria()

    assert repositorio.eliminar(1) is True
    assert repositorio.obtener_por_id(1) is None
    assert repositorio.eliminar(1) is False
    assert [categoria.id for categoria in repositorio.listar()] == [2, 3]


def test_listar_por_nombre_ignora_acentos() -> None:
    repositorio = CategoriaRepositorioMemoria()

    categorias = repositorio.listar(CategoriaConsulta(nombre="mÍni"))

    assert [categoria.id for categoria in categorias] == [3]
