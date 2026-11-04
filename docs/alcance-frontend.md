# Alcance del frontend — tienda pública y administración

## Actualización recibida

Fuente: tabla «Operación / Tienda pública / Administrador» de la imagen enviada por el usuario. Complementa los 16 elementos asignados originalmente; no los reemplaza. Esta actualización documenta requisitos, no implica que las pantallas ya estén implementadas.

| Operación | Tienda pública | Administrador |
| --- | --- | --- |
| Consultar productos | Sí | Sí |
| Consultar categorías | Sí | Sí |
| Consultar colecciones | Sí | Sí |
| Crear productos | No | Sí |
| Editar productos | No | Sí |
| Eliminar/desactivar productos | No | Sí |
| Gestionar categorías | No | Sí |
| Gestionar colecciones | No | Sí |
| Gestionar existencias | No | Sí |

## Nuestra parte: interfaces HTML, CSS y TypeScript

### Tienda pública

- Consultar el catálogo y el detalle de los productos.
- Consultar categorías y filtrar productos por ellas.
- Consultar colecciones y los productos de cada colección.
- Mantener las pantallas de inicio, carrito/revisión, acceso, ayuda, reseñas, compartir y devoluciones previstas en los requisitos originales.
- No mostrar herramientas para crear, editar, eliminar/desactivar productos o gestionar categorías, colecciones y existencias.

Estado: catálogo y filtro de categorías con datos de ejemplo; colección editorial visual y carrito/revisión de demostración. Detalle de producto, catálogo de categorías/colecciones reales y conexión API pendientes. La colección editorial no equivale todavía a gestionar ni consultar colecciones como entidades.

### Administración

Propuesta de pantallas derivada de las operaciones confirmadas:

- Acceso y estructura de panel administrativo.
- Productos: tabla de consulta, formulario de alta/edición y confirmación para eliminar/desactivar.
- Categorías: consulta y controles de gestión.
- Colecciones: consulta y controles de gestión.
- Existencias: consulta y formulario para el ajuste que autorice el backend.
- Reportes de ventas ya contemplados en la asignación original.

Estado: estructura del panel, navegación y consulta de productos/categorías de ejemplo implementadas. Pantalla de acceso implementada sin autenticación real. Alta, edición, eliminación/desactivación, gestión de categorías/colecciones/existencias y reportes siguen pendientes. Los campos de formularios, reglas y acciones exactas se acordarán con el equipo. No asumir que eliminar y desactivar significan lo mismo; confirmar cuál operación admite la API y sus restricciones.

## Reparto con backend

Frontend: presentación, navegación, formularios, validación de experiencia de usuario, tablas, confirmaciones, estados y consumo de API con fetch.
Backend Python: autenticar, determinar rol/permisos, autorizar cada operación, validar datos y reglas de negocio, actualizar stock y comunicarse con PostgreSQL.

Ocultar botones o separar rutas no asegura los permisos. El backend debe rechazar las operaciones administrativas no autorizadas; el frontend debe mostrar los errores correspondientes y no simular una sesión administrativa como si fuera real.

Pendiente acordar: mecanismo de sesión, respuesta de usuario/rol, acceso denegado, contratos de productos/categorías/colecciones/existencias, campos, paginación y estructura de errores. No hay endpoints confirmados aún.

## Orden propuesto de trabajo

1. Pantalla de acceso y estructura visual separada de tienda/panel. Cualquier modo de prueba debe estar identificado como demostración.
2. Administración de productos: tabla y formularios con datos de prueba; contrato propuesto para discutir con backend.
3. Gestión de categorías, colecciones y existencias.
4. Completar detalle de producto y navegación pública por categorías/colecciones.
5. Completar pendientes originales: reportes, reseñas, compartir, devoluciones y portafolios tras aclarar su definición.
6. Integrar API, validar permisos reales y revisar flujos y errores.

## Criterios de revisión

- La tienda pública permite consultar los tres tipos de entidades sin controles administrativos.
- El panel ofrece las operaciones de la matriz según la sesión autorizada por backend.
- Formularios muestran errores por campo y resultados; no anuncian éxito si la API falla.
- Tablas contemplan carga, vacío y error; diseño usable en móvil y con teclado.
- Una respuesta de sesión ausente o permiso insuficiente no concede acceso a datos ni operaciones.
- Las simulaciones permanecen identificadas y separadas del cliente de API real.
