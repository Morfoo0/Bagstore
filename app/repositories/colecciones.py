from dataclasses import dataclass, replace

from app.schemas.common import Estado


@dataclass(frozen=True, slots=True)
class ColeccionAlmacenada:
    id: int
    nombre: str
    slug: str
    estado: Estado
    producto_ids: tuple[int, ...] = ()


COLECCIONES_INICIALES = (
    ColeccionAlmacenada(
        1,
        "La Colección",
        "la-coleccion",
        Estado.ACTIVO,
        (1, 3, 6, 8),
    ),
    ColeccionAlmacenada(
        2,
        "Archivo",
        "archivo",
        Estado.INACTIVO,
        (2,),
    ),
)


class ColeccionRepositorioMemoria:
    def __init__(
        self,
        colecciones: tuple[ColeccionAlmacenada, ...] | None = None,
    ) -> None:
        datos = colecciones if colecciones is not None else COLECCIONES_INICIALES
        self._colecciones = {coleccion.id: coleccion for coleccion in datos}

    def listar(self) -> list[ColeccionAlmacenada]:
        return list(self._colecciones.values())

    def obtener_por_id(self, coleccion_id: int) -> ColeccionAlmacenada | None:
        return self._colecciones.get(coleccion_id)

    def obtener_por_slug(self, slug: str) -> ColeccionAlmacenada | None:
        objetivo = slug.strip().lower()
        for coleccion in self._colecciones.values():
            if coleccion.slug == objetivo:
                return coleccion
        return None

    def listar_por_producto(
        self, producto_id: int
    ) -> list[ColeccionAlmacenada]:
        return [
            coleccion
            for coleccion in self._colecciones.values()
            if producto_id in coleccion.producto_ids
        ]

    def eliminar_producto_de_todas(self, producto_id: int) -> None:
        for coleccion_id, coleccion in list(self._colecciones.items()):
            if producto_id in coleccion.producto_ids:
                producto_ids = tuple(
                    identificador
                    for identificador in coleccion.producto_ids
                    if identificador != producto_id
                )
                self._colecciones[coleccion_id] = replace(
                    coleccion, producto_ids=producto_ids
                )
