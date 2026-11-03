# Entrega 2 — Página de carrito y revisión

## Referencia y cambios

Se revisó visualmente https://mx.todomoda.com/checkout/cart/ con un producto de prueba. Se tomó como referencia la distribución de productos a la izquierda y resumen a la derecha, cupón desplegable, cantidades, opción de regalo, progreso de envío y botón de continuar. Se conserva identidad y paleta propias de Bagstore.

Se reemplazó el panel lateral por la ruta #carrito y se agregó #checkout como revisión de selección. El botón Continuar compra abre esa revisión; Finalizar demostración muestra explícitamente que no se creó un pedido ni hubo cobro.

## Funcionamiento

- Tabla de productos con ilustración, nombre, color, referencia, precio, cantidad y subtotal. En celular se presenta como tarjetas.
- Agregar, quitar y eliminar; máximo de prueba de diez unidades por modelo.
- Resumen con subtotal, descuento de ejemplo y total provisional. Envío por calcular.
- BEIGE10 aplica un 10% de descuento de ejemplo. Se pueden retirar el cupón o corregir un código inválido.
- Indicador de meta de envío de $1,000 identificado como ejemplo, sin promesa de envío gratis real.
- Selección para regalo visible en el siguiente paso.
- Solo los productos y cantidades se guardan en localStorage con validación al leerlos. Cupón y opción de regalo viven en memoria; se reinician al recargar. No se guardan credenciales ni datos de pago.
- Navegación a catálogo, regreso a carrito y revisión, con soporte de historial por hash.

## Archivos

src/components/cart.ts separa la lógica del carrito de src/main.ts; src/cart.css contiene su diseño; index.html contiene las nuevas vistas.

## Verificación

- npm run build: correcto.
- Navegador: subtotal de $948 por dos modelos; cupón de $94.80 y total provisional de $853.20; opción regalo y descuento reflejados en revisión.
- Finalizar demostración muestra mensaje sin crear pedido.
- Recargar conserva productos; añadir una unidad lleva el subtotal de $948 a $1,547 y quitarla restaura $948.
- Diseño revisado a 1440 y 390 px, sin desbordamiento horizontal en celular.
- Consola sin errores durante estos flujos.

## Pendiente de backend

Validación real de precios, stock, cupones, envío, sesiones, creación de pedidos y pagos. El carrito permanece como demostración de frontend.

Esta entrega sustituye la descripción de carrito en memoria y panel lateral de docs/avance-01.md.
