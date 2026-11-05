from pathlib import Path
from typing import Protocol


class AlmacenamientoImagen(Protocol):
    def guardar(self, contenido: bytes, clave: str) -> str:
        ...

    def eliminar(self, clave: str) -> None:
        ...


class AlmacenamientoLocal:
    def __init__(self, directorio: str, base_url: str) -> None:
        self._directorio = Path(directorio).resolve()
        self._base_url = base_url.rstrip("/")
        self._directorio.mkdir(parents=True, exist_ok=True)

    def guardar(self, contenido: bytes, clave: str) -> str:
        destino = self._resolver_clave(clave)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        return self.url_publica(clave)

    def eliminar(self, clave: str) -> None:
        destino = self._resolver_clave(clave)
        destino.unlink(missing_ok=True)

    def url_publica(self, clave: str) -> str:
        return f"{self._base_url}/{clave.replace('\\', '/')}"

    def _resolver_clave(self, clave: str) -> Path:
        relativa = Path(clave)
        if relativa.is_absolute() or ".." in relativa.parts:
            raise ValueError("Clave de almacenamiento inválida.")
        destino = (self._directorio / relativa).resolve()
        if self._directorio not in destino.parents:
            raise ValueError("Clave de almacenamiento inválida.")
        return destino
