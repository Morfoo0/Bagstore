# Entrega 6 — Recorridos del frontend

## Implementado localmente

- Fuente compartida entre panel y tienda: alta, edición, foto, categoría, color y activación se reflejan en el catálogo. Desactivar retira el producto y ajusta el carrito.
- Detalle de producto con imagen, precio, color, cantidad, existencias de prueba, reseñas y compartir. Copiar enlace tiene alternativa manual; una URL localhost solo funciona en esta computadora.
- Colecciones: alta, edición, asociaciones por ID y activación/desactivación con confirmación; consulta pública de sus productos activos.
- Inventario: búsqueda, filtro de stock bajo, ajustes enteros con motivo e historial. Cada producto inicia con 20 unidades ficticias; no es stock real.
- Reportes: pedidos locales de prueba, rango de fechas, indicadores y descarga CSV con escape de comillas y fórmulas.
- Reseñas: listado, promedio, estrellas y formulario validado. Son opiniones locales sin compra verificada; los textos se escapan al mostrarse.
- Devoluciones: solicitud vinculada a un producto comprado en un pedido de prueba, historial y estados administrativos. No genera reembolsos ni repone inventario automáticamente.
- Compra: carrito → revisión → entrega → pago de prueba → confirmación. Recogida $0 o envío ficticio $79; cupón BEIGE10 de ejemplo. Código postal ficticio; no se captura domicilio ni información bancaria. Confirmar valida productos/cantidades, calcula centavos y descuenta stock local sin efectuar cobros/envíos.
- Portafolio visual de colecciones como propuesta. El significado escolar de «portafolios» sigue por confirmar.
- Cliente fetch reutilizable: JSON, cancelación por tiempo límite, errores de conexión/401/403 y rutas configurables. Pantalla de comprobación de conexión solo llama al endpoint de salud explícitamente configurado. No hay integración real de productos/pedidos/sesiones aún.

## Mapa

- src/components/features.ts y src/features.css: nuevas pantallas y estilos adaptables.
- src/services/commerce.ts: estado local, colecciones, inventario, reseñas, pedidos y devoluciones.
- src/services/api.ts y .env.example: preparación de conexión HTTP.
- src/components/product-manager.ts: publica productos activos en la fuente compartida.
- src/components/cart.ts: límites de stock y acceso al recorrido de compra.
- tests/frontend.test.ts: pruebas de interacción DOM con jsdom y esbuild.
- tests/commerce.test.ts y tests/api.test.ts: reglas de demostración y errores HTTP.

## Validación ejecutada

`npm test`: 35 pruebas aprobadas (17 previas, 8 de interacción DOM, 6 de comercio, 4 de API).
`npm run build`: TypeScript y compilación Vite correctos.

Las pruebas de DOM cubren sincronización de productos, alta/edición/desactivación, colores duplicados, categorías, colecciones, stock agotado, reseñas como texto, alternativa de compartir, compra→reporte→devolución y API sin configuración. No equivalen a renderizar un navegador real. La API se prueba con fetch simulado, no con Python.

## Pendientes reales

1. Revisión visual de estas pantallas en móvil/escritorio, navegación por teclado, selector/decodificación de fotos reales y compartir nativo. El control del navegador no estuvo disponible en esta sesión; no se declara revisión visual completada.
2. Acordar e integrar endpoints/JSON, sesión y roles protegidos en servidor, CORS, imágenes y errores de negocio. El panel actual es una demostración pública, nunca un área segura de datos reales.
3. Datos definitivos: marca, fotos, especificaciones, tarifas y políticas. Confirmar portafolios y campos finales de entrega/pago con el equipo.
4. Pedidos, pagos, stock y devoluciones reales validados por Python/PostgreSQL. El estado local sirve exclusivamente para revisar frontend.

GitHub continúa pausado por instrucción del usuario. No hacer push ni abrir PR hasta nueva autorización.
