# Comparación con la rama backend

Revisión de código, sin ejecutar el servidor ni modificar la rama remota.
Snapshot revisado: 5db5cc94dad8ec70c966bdc566d13754ab9278f2.
Fuentes: [README](https://github.com/Morfoo0/Bagstore/blob/5db5cc94dad8ec70c966bdc566d13754ab9278f2/README.md), [contrato borrador 0.2.0](https://github.com/Morfoo0/Bagstore/blob/5db5cc94dad8ec70c966bdc566d13754ab9278f2/docs/api-contract.md), schemas, rutas, servicios y configuración de esa revisión.

## Alcance real

FastAPI ofrece /api/health y CRUD de /api/productos, /api/categorias y /api/colecciones. Persistencia temporal en memoria; reiniciar pierde cambios. No existen rutas de cuentas/sesión, pedidos, pagos, reportes, reseñas, devoluciones o envíos. No hay conexión PostgreSQL todavía.

## Adaptaciones del frontend

| Área | Diferencia y trabajo necesario |
| --- | --- |
| Cliente HTTP | Nuestra actualización genérica usa PATCH; backend usa PUT con cuerpo completo. Agregar GET detalle y DELETE. Leer listas desde datos y paginacion, no como arreglos planos. |
| Productos | Mapear nombre/precio/categoria/estado y separar resumen de listado de detalle. Formulario debe incorporar SKU obligatorio al crear e inmutable después, descripción, existencias y arreglo de imágenes. IDs numéricos del servidor sustituyen IDs locales de categorías/colecciones. |
| Validación | Alinear límites y campos permitidos. RequestSchema rechaza extras: no enviar colorId, label, tonos SVG, imageData ni otros campos exclusivamente locales. |
| Imágenes | Backend admite hasta 10 objetos con URL HTTP(S), texto alternativo, orden y principal. Nuestro JPEG data URL no es compatible; acordar subida de archivos o usar URLs alojadas. No perder imágenes al enviar PUT: exige arreglo completo. |
| Colores | No existe recurso ni campo de color. Ampliar contrato con backend para mantener colores normalizados y filtro por ID; no eliminar silenciosamente este requisito. |
| Catálogo | Búsqueda/filtros/paginación/orden en servidor: nombre, categoria_id o categoria, coleccion_id o coleccion, disponible, pagina, por_pagina y orden. No combinar ID y slug del mismo filtro. Agotados activos deben seguir visibles. |
| Existencias | Leer existencias del detalle y disponible del resumen. Retirar 20 unidades por defecto en modo API. PUT establece cantidad absoluta; no hay historial de movimientos, motivos persistidos, reservas ni descuento por compra. Acordar endpoint seguro para ajustes y concurrencia. |
| Categorías | Backend agrega descripción, orden, estado y slug. DELETE físico bloqueado con 409 si hay productos asociados. No tratarlo como desactivación reversible. |
| Colecciones | Guardar asociaciones solo en producto_ids del POST/PUT de colección. Detalle no devuelve IDs/productos embebidos; consultar /api/productos?coleccion_id=... paginado para reconstruir asociaciones visibles. Ampliar respuesta administrativa para membresía completa, incluyendo inactivos. Agregar portada URL y estados. |
| Borrado de producto | DELETE es borrado lógico y retira asociaciones; no equivale a nuestro desactivar/reactivar preservando relaciones. Para cambiar estado usar PUT completo; acordar recuperación de eliminados. |
| Errores | Interpretar error.codigo, error.mensaje y error.detalles[{campo,mensaje}], y mapearlos a campos. Manejar 400/401/403/404/409/422/500 sin anunciar éxito en fallos. |
| CORS | Frontend usa http://127.0.0.1:5173; configuración por defecto del backend solo permite localhost:3000/5173. Añadir origen exacto o ejecutar ambos con localhost. |

## Bloqueos del backend

- requiere_administrador actualmente no valida nada: escrituras abiertas. Las rutas GET llaman servicios con es_administrador=False; estado=todos/inactivo responde 403 y detalles inactivos 404. El panel no podrá consultar/reactivar inactivos por API hasta conectar la autorización administrativa.
- El contrato solo describe rol administrador y visitantes; nuestra compra exige cliente registrado. Acordar registro, login, logout, sesión y rol/identidad de cliente. Mantener el bloqueo actual de compra hasta sesión verificada.
- Colores normalizados/filtros y subida de fotos aún sin soporte.
- Pedidos con líneas históricas, comprador/dirección, totales calculados por servidor, pagos y stock transaccional pendientes. Cupones/regalo son acuerdos por incorporar.
- Reportes, detalle/ticket real, guía y paquetería necesitan recursos de pedidos/envíos. El ticket visual se reutiliza, pero no prueba pago ni crea una etiqueta.
- Reseñas y devoluciones requieren contratos, pertenencia a usuario y permisos.
- PostgreSQL y persistencia son trabajo del equipo backend; no resolver con escrituras locales del navegador.

## Orden recomendado

1. Acordar contrato de colores/imágenes y permiso administrativo; resolver origen CORS.
2. Conectar primero catálogo público (salud, categorías, productos, detalle, colecciones) con tipos y validación de respuesta, carga/vacío/error y paginación.
3. Adaptar formularios y escrituras administrativas al contrato PUT, errores y autorización real. No habilitar escrituras públicas por el no-op actual.
4. Integrar cuentas/cliente; después pedidos, inventario transaccional, entregas y pagos.
5. Integrar reportes, ticket/guías, reseñas y devoluciones con sus nuevos recursos.

La revisión no verifica que el servidor esté ejecutándose ni prueba endpoints en vivo. No se fusionaron ramas ni se subió nada a GitHub. Esta comparación sustituye la suposición anterior de que no había rutas de catálogo disponibles; las demás áreas continúan pendientes.
