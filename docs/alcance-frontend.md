> Estado vigente: entrega 6. Panel y tienda comparten productos locales. Detalle, colecciones, inventario, reportes, reseñas, compartir, devoluciones y compra de prueba implementados. API real, sesión/roles y revisión visual nueva pendientes. Consultar docs/avance-06-recorridos-frontend.md y docs/contrato-api-propuesto.md. GitHub continúa pausado.

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

Estado: estructura del panel, acceso visual, alta/edición de productos con foto, desactivar/reactivar y filtros implementados como demostración local. Categorías permite alta y renombrado; el producto selecciona colores compartidos y permite agregarlos desde el formulario, sin duplicados por mayúsculas/espacios/acentos. IDs estables conservan relaciones. Colecciones, existencias, reportes, eliminación definitiva y autenticación/permisos reales siguen pendientes. Los campos y contratos definitivos se acordarán con el equipo. No asumir que eliminar y desactivar significan lo mismo.

## Acuerdo de colores y categorías

Color: identificador estable, nombre normalizado para detectar duplicados y tono hexadecimal de muestra. Categoría: identificador estable y nombre. El producto guarda categoryId/colorId; los tonos del dibujo son campos decorativos aparte. Propuesta para el contrato Python: categoria_id y color_id como referencias, con nombres obtenidos de sus catálogos. Estos nombres de campos son una propuesta, no endpoints acordados.

La tienda pública incorpora filtros con las mismas opciones de categorías/colores. Los productos del panel siguen siendo datos de prueba independientes de los cuatro productos públicos hasta integrar una fuente común. Opciones nuevas sin productos públicos muestran un resultado vacío.

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
