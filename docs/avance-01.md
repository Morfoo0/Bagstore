# Entrega 1 — Base visual pública

## Implementado

- Inicio con identidad provisional Bagstore y paleta Beige clásico.
- Encabezado, buscador, navegación por secciones, menú móvil y pie de página.
- Colección editorial y cuatro productos ficticios con ilustraciones SVG propias.
- Catálogo con filtros por categoría, búsqueda y estado sin resultados.
- Carrito local en memoria: agregar, cambiar cantidades, eliminar y subtotal ilustrativo en MXN. Se reinicia al recargar.
- Ventanas modales nativas con cierre, navegación por teclado y gestión de foco al cambiar el carrito.
- Ayuda/acerca de mediante preguntas frecuentes.

## Mapa de archivos

| Archivo | Función |
| --- | --- |
| index.html | Estructura semántica, secciones y ventanas modales |
| src/styles.css | Paleta, distribución y adaptación móvil/escritorio |
| src/main.ts | Búsqueda, filtros, menú, carrito y ventanas informativas |
| src/types/product.ts | Tipos de productos y categorías |
| src/data/products.ts | Datos ficticios separados de la interfaz |
| src/components/bag.ts | Ilustración SVG reutilizable de bolsas |
| package.json | Comandos de desarrollo y compilación |
| tsconfig.json | Revisión estricta de TypeScript |
| docs/diseno.md | Paleta elegida por el usuario |

## Verificación realizada

- npm run build: revisión TypeScript y compilación Vite correctas.
- Servidor local: respuesta HTTP 200.
- Navegador: filtro Tote muestra dos productos; búsqueda inexistente muestra estado vacío; limpiar recupera cuatro productos.
- Carrito: agregar Tote Everyday muestra $599; incrementar muestra dos unidades y $1,198; eliminar muestra estado vacío.
- Menú móvil: abre y cierra al elegir una sección; comprobación a 390 px sin desbordamiento horizontal.
- Revisión visual a 390 y 1440 px. Consola del navegador sin errores durante los flujos comprobados.
- No se ha realizado una auditoría integral de accesibilidad ni pruebas con backend real.

## Pendiente

Pantalla de acceso real, detalle de producto, reseñas, compartir, formulario de devoluciones, reportes administrativos y portafolios definitivos. La sección de colección es una propuesta visual; el significado académico de portafolios debe confirmarse.

No hay servicio fetch ni endpoints definitivos todavía: la API Python no se ha acordado. Implementar el adaptador de API al definir contratos; no presentar esta entrega como integrada al backend.
La validación real de sesiones, permisos, precios, stock y pagos corresponde al backend.

Nombre comercial, imágenes, productos reales y políticas comerciales pendientes de definir. No se publicará una tienda en internet en esta etapa; el trabajo permanece como frontend local para integrar con el equipo.
