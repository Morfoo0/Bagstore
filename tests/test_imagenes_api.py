from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.imagen import ImagenProducto


def png_bytes(color: str = "red", size: tuple[int, int] = (10, 10)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def subir_imagen(
    client: TestClient,
    producto_id: int,
    *,
    contenido: bytes | None = None,
    nombre: str = "imagen.png",
    content_type: str = "image/png",
    texto_alternativo: str | None = "Imagen de prueba",
    orden: int | None = None,
    es_principal: bool = False,
):
    data = {}
    if texto_alternativo is not None:
        data["texto_alternativo"] = texto_alternativo
    if orden is not None:
        data["orden"] = str(orden)
    if es_principal:
        data["es_principal"] = "true"
    return client.post(
        f"/api/productos/{producto_id}/imagenes",
        files={
            "archivo": (
                nombre,
                contenido if contenido is not None else png_bytes(),
                content_type,
            )
        },
        data=data,
    )


def test_subir_imagen_genera_url_permanente(
    admin_client: TestClient,
    db_session: Session,
) -> None:
    response = subir_imagen(
        admin_client,
        6,
        texto_alternativo="Bolsa roja",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["producto_id"] == 6
    assert body["url"].startswith("http://testserver/media/productos/6/")
    assert "C:\\" not in body["url"]
    assert body["orden"] == 1
    assert body["es_principal"] is True
    assert body["texto_alternativo"] == "Bolsa roja"

    db_session.expire_all()
    imagen = db_session.scalars(
        select(ImagenProducto).where(ImagenProducto.id == body["id"])
    ).first()
    assert imagen is not None
    assert imagen.storage_key is not None
    archivo = Path(settings.upload_dir) / imagen.storage_key
    assert archivo.exists()

    detalle = admin_client.get("/api/productos/6").json()
    assert detalle["imagenes"][0]["url"] == body["url"]

    ruta_publica = body["url"].replace("http://testserver", "")
    assert admin_client.get(ruta_publica).status_code == 200


def test_subir_imagen_rechaza_archivo_invalido(
    admin_client: TestClient,
) -> None:
    response = subir_imagen(
        admin_client,
        6,
        contenido=b"esto no es una imagen",
    )

    assert response.status_code == 422
    assert response.json()["error"]["codigo"] == "ARCHIVO_INVALIDO"


def test_subir_imagen_rechaza_archivo_demasiado_grande(
    admin_client: TestClient,
) -> None:
    response = subir_imagen(
        admin_client,
        6,
        contenido=b"x" * (settings.max_image_size_bytes + 1),
    )

    assert response.status_code == 413
    assert (
        response.json()["error"]["codigo"]
        == "ARCHIVO_DEMASIADO_GRANDE"
    )


def test_subir_imagen_rechaza_orden_duplicado(
    admin_client: TestClient,
) -> None:
    assert subir_imagen(admin_client, 6, orden=1).status_code == 201

    response = subir_imagen(admin_client, 6, orden=1)

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "orden"


def test_imagen_principal_y_actualizacion_de_metadatos(
    admin_client: TestClient,
) -> None:
    primera = subir_imagen(
        admin_client,
        6,
        texto_alternativo="Primera",
        es_principal=True,
    ).json()
    segunda = subir_imagen(
        admin_client,
        6,
        texto_alternativo="Segunda",
    ).json()

    assert primera["es_principal"] is True

    actualizada = admin_client.put(
        f"/api/productos/6/imagenes/{segunda['id']}",
        json={
            "texto_alternativo": "Segunda principal",
            "orden": 0,
            "es_principal": True,
        },
    )

    assert actualizada.status_code == 200
    imagenes = admin_client.get("/api/productos/6").json()["imagenes"]
    assert [imagen["orden"] for imagen in imagenes] == [0, 1]
    assert sum(imagen["es_principal"] for imagen in imagenes) == 1
    assert imagenes[0]["texto_alternativo"] == "Segunda principal"
    assert imagenes[0]["es_principal"] is True


def test_eliminar_imagen_borra_archivo(
    admin_client: TestClient,
    db_session: Session,
) -> None:
    creada = subir_imagen(admin_client, 6).json()
    db_session.expire_all()
    imagen = db_session.scalars(
        select(ImagenProducto).where(ImagenProducto.id == creada["id"])
    ).first()
    assert imagen is not None
    archivo = Path(settings.upload_dir) / imagen.storage_key
    assert archivo.exists()

    response = admin_client.delete(
        f"/api/productos/6/imagenes/{creada['id']}"
    )

    assert response.status_code == 204
    assert response.content == b""
    assert not archivo.exists()
    assert admin_client.get("/api/productos/6").json()["imagenes"] == []


def test_no_se_puede_eliminar_imagen_de_otro_producto(
    admin_client: TestClient,
) -> None:
    creada = subir_imagen(admin_client, 6).json()

    response = admin_client.delete(
        f"/api/productos/1/imagenes/{creada['id']}"
    )

    assert response.status_code == 404


def test_maximo_de_imagenes_por_producto(
    admin_client: TestClient,
) -> None:
    for indice in range(10):
        response = subir_imagen(
            admin_client,
            7,
            texto_alternativo=f"Imagen {indice}",
        )
        assert response.status_code == 201

    response = subir_imagen(admin_client, 7, texto_alternativo="Extra")

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "imagenes"


def test_subida_de_imagenes_requiere_admin(
    public_client: TestClient,
    cliente_client: TestClient,
) -> None:
    publico = subir_imagen(public_client, 6)
    cliente = subir_imagen(cliente_client, 6)

    assert publico.status_code == 401
    assert cliente.status_code == 403


def test_actualizar_imagen_rechaza_orden_duplicado(
    admin_client: TestClient,
) -> None:
    primera = subir_imagen(admin_client, 6, orden=1).json()
    segunda = subir_imagen(admin_client, 6, orden=2).json()

    response = admin_client.put(
        f"/api/productos/6/imagenes/{segunda['id']}",
        json={
            "texto_alternativo": segunda["texto_alternativo"],
            "orden": primera["orden"],
            "es_principal": False,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["detalles"][0]["campo"] == "orden"
