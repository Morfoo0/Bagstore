from dataclasses import dataclass

from app.schemas.common import Estado


@dataclass(frozen=True, slots=True)
class CategoriaAlmacenada:
    id: int
    nombre: str
    slug: str
    estado: Estado


CATEGORIAS_INICIALES = (
    CategoriaAlmacenada(1, "Cross Body", "cross-body", Estado.ACTIVO),
    CategoriaAlmacenada(2, "Tote Bags", "tote-bags", Estado.ACTIVO),
    CategoriaAlmacenada(3, "Mini Bags", "mini-bags", Estado.ACTIVO),
)


class CategoriaRepositorioMemoria:
    def __init__(
        self,
        categorias: tuple[CategoriaAlmacenada, ...] | None = None,
    ) -> None:
        datos = categorias if categorias is not None else CATEGORIAS_INICIALES
        self._categorias = {categoria.id: categoria for categoria in datos}

    def listar(self) -> list[CategoriaAlmacenada]:
        return list(self._categorias.values())

    def obtener_por_id(self, categoria_id: int) -> CategoriaAlmacenada | None:
        return self._categorias.get(categoria_id)

    def obtener_por_slug(self, slug: str) -> CategoriaAlmacenada | None:
        objetivo = slug.strip().lower()
        for categoria in self._categorias.values():
            if categoria.slug == objetivo:
                return categoria
        return None
