from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import RolUsuario
from app.core.security import hash_password, normalizar_email
from app.core.text import normalizar_texto
from app.models.categoria import Categoria
from app.models.coleccion import Coleccion
from app.models.imagen import ImagenProducto
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.repositories.categorias import CATEGORIAS_INICIALES
from app.repositories.colecciones import COLECCIONES_INICIALES
from app.repositories.productos import (
    ProductoConsulta,
    ProductoRepositorioMemoria,
)
from app.schemas.common import Estado, EstadoFiltro


def crear_admin(
    session: Session,
    email: str,
    password: str,
    nombre: str = "Administrador",
) -> Usuario:
    email_normalizado = normalizar_email(email)
    existente = session.scalars(
        select(Usuario).where(Usuario.email == email_normalizado)
    ).first()
    if existente is not None:
        return existente

    admin = Usuario(
        nombre=nombre,
        email=email_normalizado,
        telefono=None,
        password_hash=hash_password(password),
        rol=RolUsuario.ADMINISTRADOR,
        estado=Estado.ACTIVO,
    )
    session.add(admin)
    session.flush()
    return admin


def seed_catalogo(session: Session) -> None:
    if session.scalar(select(func.count(Categoria.id))):
        return

    categorias: dict[int, Categoria] = {}
    for categoria in CATEGORIAS_INICIALES:
        entidad = Categoria(
            nombre=categoria.nombre,
            nombre_busqueda=normalizar_texto(categoria.nombre),
            slug=categoria.slug,
            descripcion=categoria.descripcion,
            estado=categoria.estado,
            orden=categoria.orden,
            creado_en=categoria.creado_en,
            actualizado_en=categoria.actualizado_en,
        )
        session.add(entidad)
        session.flush()
        categorias[categoria.id] = entidad

    repositorio_memoria = ProductoRepositorioMemoria()
    productos_memoria = sorted(
        repositorio_memoria.listar(
            ProductoConsulta(estado=EstadoFiltro.TODOS)
        ),
        key=lambda producto: producto.id,
    )
    productos: dict[int, Producto] = {}
    for producto in productos_memoria:
        entidad = Producto(
            nombre=producto.nombre,
            nombre_busqueda=normalizar_texto(producto.nombre),
            slug=producto.slug,
            descripcion=producto.descripcion,
            precio=producto.precio,
            sku=producto.sku,
            categoria_id=categorias[producto.categoria_id].id,
            existencias=producto.existencias,
            estado=producto.estado,
            creado_en=producto.creado_en,
            actualizado_en=producto.actualizado_en,
            imagenes=[
                ImagenProducto(
                    url=imagen.url,
                    texto_alternativo=imagen.texto_alternativo,
                    orden=imagen.orden,
                    es_principal=imagen.es_principal,
                )
                for imagen in producto.imagenes
            ],
        )
        session.add(entidad)
        session.flush()
        productos[producto.id] = entidad

    for coleccion in COLECCIONES_INICIALES:
        entidad = Coleccion(
            nombre=coleccion.nombre,
            nombre_busqueda=normalizar_texto(coleccion.nombre),
            slug=coleccion.slug,
            descripcion=coleccion.descripcion,
            estado=coleccion.estado,
            imagen_portada_url=coleccion.imagen_portada_url,
            creado_en=coleccion.creado_en,
            actualizado_en=coleccion.actualizado_en,
            productos=[
                productos[producto_id]
                for producto_id in coleccion.producto_ids
                if producto_id in productos
            ],
        )
        session.add(entidad)
        session.flush()

    session.flush()


def seed_desarrollo(session: Session) -> None:
    seed_catalogo(session)
    if settings.admin_password:
        crear_admin(
            session,
            settings.admin_email,
            settings.admin_password,
        )


def main() -> None:
    with SessionLocal() as session:
        seed_desarrollo(session)
        session.commit()
    print("Datos iniciales cargados.")


if __name__ == "__main__":
    main()
