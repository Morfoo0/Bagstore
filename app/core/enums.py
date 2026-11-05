from enum import Enum


class RolUsuario(str, Enum):
    CLIENTE = "cliente"
    ADMINISTRADOR = "administrador"
