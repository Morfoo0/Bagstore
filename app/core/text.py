import unicodedata


def normalizar_texto(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor.casefold())
    return "".join(
        caracter
        for caracter in normalizado
        if not unicodedata.combining(caracter)
    )
