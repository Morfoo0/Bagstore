# Entrega 9 — Detalles del pedido y ticket de preparación

Reportes agrega una columna Acciones con Detalles. Abre un diálogo con el ID/fecha del pedido, método de entrega/pago seleccionado, referencias de productos, nombres, cantidades, precios, importes, subtotal, descuento, envío y total. Usa la información guardada en el pedido, no nombres/precios actuales del catálogo. Los pedidos nuevos conservan además el color; los anteriores sin ese campo indican que no se registró.

Ticket con casillas para marcar productos al preparar, total de unidades y espacios para preparó/revisó. Imprimir ticket abre la impresión del navegador, que permite seleccionar impresora o Guardar como PDF. CSS de impresión exclusivo del documento, sin menú, formularios ni botones, con tablas y saltos de página adaptados.

Para entrega a domicilio se puede vincular una guía existente mediante paquetería y número de guía. Se asocia al ID de pedido en bagstore.shipment-references.v1 y se incluye al imprimir. Los errores de recuperación/guardado se muestran sin anunciar éxito. La referencia persiste en este navegador, sin integración con una paquetería ni contratación/generación de etiquetas.

Los pedidos locales no tienen destinatario/dirección: se informa su ausencia. No se inventan datos de entrega, comprobación de pago ni códigos de barras. El documento es un ticket de preparación de vista previa, no factura ni etiqueta oficial.

Pendiente con backend: detalle autorizado por rol, datos históricos de producto/color/SKU, destinatario/domicilio, estado de pago, relación de pedido y envío/guía, paquetería y etiqueta oficial. Si un pedido se divide en varios paquetes, acordar envío→líneas/cantidades: esta primera interfaz solo admite una referencia por pedido y no modela envíos parciales.

Pruebas de interacción: abrir/cerrar, productos históricos y escape HTML, totales, guardado/recuperación de guía, impresión solicitada con window.print simulado, limpieza de estado y almacenamiento corrupto. Pendiente comprobar el resultado físico/PDF y la vista móvil en navegador real. No se imprimió un documento físicamente.

La compra pública sigue exigiendo API de cuentas. Se pueden consultar pedidos locales existentes; los fixtures de pruebas no se agregan al navegador del usuario. GitHub permanece pausado.

Validación ejecutada: npm test, 39 pruebas correctas; npm run build y git diff --check correctos.
