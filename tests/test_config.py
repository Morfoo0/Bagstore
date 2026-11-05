import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_api_prefix_se_normaliza() -> None:
    assert Settings(api_prefix="api").api_prefix == "/api"
    assert Settings(api_prefix="/api/").api_prefix == "/api"


def test_cors_rechaza_wildcard_con_credenciales() -> None:
    with pytest.raises(ValidationError):
        Settings(
            cors_origins=["*"],
            cors_allow_credentials=True,
        )


def test_cors_normaliza_origenes_metodos_y_cabeceras() -> None:
    settings = Settings(
        cors_origins=[
            "http://localhost:3000/",
            "http://localhost:3000",
        ],
        cors_allow_methods=["get", "GET"],
        cors_allow_headers=["Content-Type", "Content-Type"],
        cors_allow_credentials=False,
    )

    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.cors_allow_methods == ["GET"]
    assert settings.cors_allow_headers == ["Content-Type"]
