# Pendientes del backend para completar la tienda

Referencia revisada: rama backend, commit 5db5cc94dad8ec70c966bdc566d13754ab9278f2. La adaptación del frontend no modifica esa rama.

## Prioridad 1 — acceso y administración

- Registro e inicio/cierre de sesión de clientes; consulta de sesión verificada, expiración y errores 401/403. Acordar cookies/tokens y CSRF si aplica.
- Autorización real por rol en escrituras. Actualmente requiere_administrador es no-op. Los botones de guardar API permanecen deshabilitados en frontend hasta contar con sesión verificada.
- Conectar el rol administrativo a GET: listado/detalle de inactivos y estado=todos. Hoy los handlers públicos no pasan es_administrador=True; no se puede consultar y reactivar desde el servidor un producto desactivado.
- Colecciones: devolver producto_ids completos en detalle administrativo o un endpoint de membresía, incluyendo productos inactivos. El frontend bloquea edición para evitar sobrescribir asociaciones desconocidas; el detalle público actual no contiene miembros.
- Definir desactivar (PUT estado=inactivo) frente a eliminar (DELETE lógico que retira asociaciones); precisar recuperación de eliminados. Categorías/colecciones usan DELETE físico y necesitan confirmación explícita al habilitarse.

## Prioridad 2 — catálogo completo

- Colores normalizados con ID, nombre y tono; relación al producto y filtro de servidor. Mantener alta integrada desde producto sin duplicados. El modo API informa que aún no hay colores y no envía campos desconocidos.
- Subida/almacenamiento de fotos y URLs permanentes. El frontend ya admite el arreglo de hasta 10 URLs HTTP(S), texto alternativo, orden y principal del contrato actual; no puede subir archivos sin endpoint.
- Persistencia PostgreSQL, migraciones, claves/restricciones y datos iniciales. La API actual pierde cambios al reiniciar.
- Ajustes de inventario con motivo/historial, permisos y control de concurrencia. Ahora PUT reemplaza una cantidad absoluta, sin movimientos ni reservas.

## Prioridad 3 — compra y posventa

- Pedidos vinculados al cliente y líneas históricas con SKU/color, nombre, cantidad y precio; estados y validación de pertenencia.
- Stock transaccional, reservas y validación de cantidades/precios al confirmar. Descuentos, cupón y regalo necesitan reglas confirmadas del servidor.
- Entrega: destinatario, domicilio, tarifas, paquetería y guía. Relación de envíos con líneas/cantidades si hay paquetes parciales; etiqueta oficial y seguimiento.
- Pagos con estado verificable, manejo de fallos/reintentos y prevención de pedidos/cobros duplicados. El frontend no debe declarar pagado por seleccionar un método.
- Reportes de ventas por fechas, métricas y detalle autorizado. Alimentan ticket/CSV reales; el ticket local no prueba pago.
- Reseñas por producto, validaciones, permisos y moderación; devoluciones vinculadas al comprador/pedido, plazos, estados y reglas de reembolso/stock.

## Despliegue e integración

El proxy de Vite resuelve el origen durante desarrollo sin cambiar el backend. En producción se necesita proxy /api en el hosting o CORS para el origen exacto del frontend, con política de credenciales acordada. Vite preview no sustituye el proxy de producción.

Definir contrato de sesión y membresía, URL de despliegue y políticas comerciales. No cambiar el contrato del catálogo sin avisar al frontend; regenerar/adaptar tipos y ejecutar pruebas de integración cuando cambie.
