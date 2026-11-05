from app.models.categoria import Categoria
from app.models.coleccion import Coleccion
from app.models.imagen import ImagenProducto
from app.models.producto import Producto
from app.models.sesion import Sesion
from app.models.usuario import Usuario
from app.repositories.categorias import CategoriaAlmacenada
from app.repositories.colecciones import ColeccionAlmacenada
from app.repositories.productos import ImagenAlmacenada, ProductoAlmacenado
from app.repositories.sesiones import SesionAlmacenada
from app.repositories.usuarios import UsuarioAlmacenado


def imagen_a_entidad(imagen: ImagenProducto) -> ImagenAlmacenada:
    return ImagenAlmacenada(
        url=imagen.url,
        texto_alternativo=imagen.texto_alternativo,
        orden=imagen.orden,
        es_principal=imagen.es_principal,
    )


def producto_a_entidad(producto: Producto) -> ProductoAlmacenado:
    imagenes = tuple(
        imagen_a_entidad(imagen)
        for imagen in sorted(producto.imagenes, key=lambda item: item.orden)
    )
    return ProductoAlmacenado(
        id=producto.id,
        nombre=producto.nombre,
        slug=producto.slug,
        descripcion=producto.descripcion,
        precio=producto.precio,
        sku=producto.sku,
        categoria_id=producto.categoria_id,
        existencias=producto.existencias,
        imagenes=imagenes,
        estado=producto.estado,
        creado_en=producto.creado_en,
        actualizado_en=producto.actualizado_en,
        eliminado_en=producto.eliminado_en,
    )


def categoria_a_entidad(categoria: Categoria) -> CategoriaAlmacenada:
    return CategoriaAlmacenada(
        id=categoria.id,
        nombre=categoria.nombre,
        slug=categoria.slug,
        estado=categoria.estado,
        descripcion=categoria.descripcion,
        orden=categoria.orden,
        creado_en=categoria.creado_en,
        actualizado_en=categoria.actualizado_en,
    )


def coleccion_a_entidad(coleccion: Coleccion) -> ColeccionAlmacenada:
    producto_ids = tuple(
        producto.id
        for producto in sorted(coleccion.productos, key=lambda item: item.id)
    )
    return ColeccionAlmacenada(
        id=coleccion.id,
        nombre=coleccion.nombre,
        slug=coleccion.slug,
        estado=coleccion.estado,
        producto_ids=producto_ids,
        descripcion=coleccion.descripcion,
        imagen_portada_url=coleccion.imagen_portada_url,
        creado_en=coleccion.creado_en,
        actualizado_en=coleccion.actualizado_en,
    )


def usuario_a_entidad(usuario: Usuario) -> UsuarioAlmacenado:
    return UsuarioAlmacenado(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        telefono=usuario.telefono,
        password_hash=usuario.password_hash,
        rol=usuario.rol,
        estado=usuario.estado,
        creado_en=usuario.creado_en,
        actualizado_en=usuario.actualizado_en,
    )


def sesion_a_entidad(sesion: Sesion) -> SesionAlmacenada:
    return SesionAlmacenada(
        id=sesion.id,
        usuario_id=sesion.usuario_id,
        token_hash=sesion.token_hash,
        creado_en=sesion.creado_en,
        expira_en=sesion.expira_en,
        revocado_en=sesion.revocado_en,
        user_agent=sesion.user_agent,
        ip=sesion.ip,
    )
