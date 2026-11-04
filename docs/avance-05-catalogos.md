# Entrega 5 — Colores compartidos y categorías configurables

## Acuerdo implementado

- Diez colores básicos: Negro, Blanco, Beige, Café, Rojo, Rosa, Azul, Verde, Gris y Multicolor. Cada opción tiene ID, nombre y muestra de tono.
- El producto selecciona un color del catálogo; no escribe un nombre libre.
- Agregar color abre un formulario pequeño desde el producto. Al guardarlo, la nueva opción queda seleccionada, sin perder el borrador ni la foto.
- Se rechazan duplicados al normalizar mayúsculas, acentos y espacios.
- Categorías permite crear nuevos tipos de bolsa y renombrarlos manteniendo el ID.
- Selector de categorías dinámico: una mochila, clutch u otro tipo ya no requiere cambiar código.
- Filtros por color en panel y tienda; selector público de tipo de bolsa con categorías compartidas.
- Los tonos de ilustración son decorativos y están separados del color usado para filtrar.

## Compatibilidad

Los productos anteriores se conservan. Arena, Lino y Beige clásico se vinculan a Beige; Caramelo/Cacao a Café. Los nombres antiguos que no corresponden a opciones básicas se incorporan al catálogo para conservarlos. Se vinculan los productos del panel a IDs estables; renombrar una categoría no rompe la relación.

Los catálogos se comparten dentro de este navegador. Los productos editados en el panel aún son un conjunto de prueba independiente de los cuatro productos públicos. Por eso una categoría/color nuevo puede no tener productos en el catálogo público. Al integrar Python se acordará la fuente de datos común y se aplicarán permisos reales.

No se eliminan categorías o colores en esta entrega. Agregar y renombrar categorías es reversible mediante otra edición; los productos conservan sus relaciones por ID.

## Archivos

- src/services/catalogs.ts: catálogos, IDs, normalización y persistencia.
- src/components/product-manager.ts: selector de color, alta integrada, categorías y filtros.
- src/services/admin-products.ts: categorías configurables y referencias estables.
- src/main.ts: filtros públicos de categorías y colores.
- tests/catalogs.test.ts: duplicados, persistencia, relaciones y compatibilidad.

## Validación

Compilación TypeScript/Vite y 17 pruebas del repositorio/productos/catálogos correctas. Se comprobaron IDs únicos y referencias HTML de los módulos. La revisión visual/interactiva sigue pendiente: la única ventana controlable en esta sesión es Codex y no se automatiza su interfaz.

## Pendiente general

Revisar en navegador los formularios, modales anidados y filtros a móvil/escritorio; después gestión de colecciones y existencias, reportes, detalle de producto, reseñas, compartir y devoluciones. Definición de portafolios y contratos de API/roles/pedidos/pagos pendientes del equipo. GitHub sigue pausado por instrucción del usuario.
