> Actualización vigente: ya se revisó y adaptó el catálogo de backend 5db5cc9. Consultar docs/avance-10-adaptacion-api.md y docs/pendientes-backend-integracion.md. Las propuestas de recursos restantes de este documento no son endpoints existentes. Configuración actual en .env.example: modo API y proxy Vite /api; no depender solo de la comprobación de salud.

# Integración de API — propuesta por acordar

El frontend sigue en demostración local. No se han confirmado rutas, modelos JSON ni mecanismo de autenticación con el equipo de Python. Esta propuesta no obliga al backend a implementar nombres concretos.

## Configuración disponible

Copiar .env.example a .env y completar VITE_API_BASE_URL y VITE_API_HEALTH_PATH con valores suministrados por el equipo. Reiniciar Vite. Desde #admin/conexion se puede comprobar la respuesta JSON de salud. Sin ambos valores no se efectúa ninguna solicitud.

Las variables VITE son públicas: nunca incluir claves privadas, credenciales de PostgreSQL ni secretos. ApiClient utiliza fetch con credentials: include; si el equipo adopta cookies, acordar CORS con origen explícito, cookie segura y protección CSRF antes de permitir escrituras. El cliente no concede roles.

## Recursos a acordar

| Recurso | Información / decisiones necesarias |
| --- | --- |
| Productos | ID estable, nombre, precio decimal, categoría/color por ID, URL de imagen, estado, búsqueda/paginación; crear/editar/desactivar solo con permiso administrativo |
| Colores y categorías | IDs estables, nombres normalizados, color hexadecimal; duplicados, alta y renombrado |
| Colecciones | ID, nombre, descripción, productos asociados, estado |
| Inventario | Cantidad disponible, ajuste con motivo, historial, concurrencia y stock insuficiente |
| Reseñas | Producto, nombre público, calificación, comentario, fecha; autorización y moderación |
| Pedidos | Líneas producto/cantidad; el servidor determina precio, descuento, envío y total; evitar pedidos duplicados al reintentar |
| Devoluciones | Pedido/producto, motivo, comentario, estados y condiciones; validar pertenencia al comprador |
| Reportes | Fechas, zona horaria, importes, unidades, permisos y paginación |
| Acceso/sesión | Inicio/cierre de sesión, expiración, rol; respuestas 401 y 403. El formulario actual nunca envía contraseñas |
| Imágenes | Multipart o carga firmada, límites, validación y URL permanente. La foto local JPEG actual no es almacenamiento de servidor |
| Salud | Ruta GET explícita y respuesta JSON; única comprobación conectable actualmente desde la interfaz |

## Cliente preparado y trabajo restante

src/services/api.ts ofrece request<T> y backendResource con rutas suministradas por el consumidor, operaciones list/create/update, tiempo límite y errores de transporte. T es una anotación TypeScript, no valida JSON en ejecución: implementar validadores/adaptadores por recurso cuando exista contrato confirmado. No basta con configurar .env para sustituir los repositorios locales.

El cliente distingue 401, 403, fallo de red/CORS, tiempo agotado y JSON inválido. Proponer con backend una respuesta de errores de campo y códigos de negocio (stock, precio, duplicados), evitando exponer excepciones internas. Los mensajes actuales son genéricos; el mapeo de errores de negocio sigue pendiente.

Antes de conectar: confirmar esquema, moneda/centavos, zona horaria, permisos, política de imágenes y CSRF. Después reemplazar cada repositorio local, probar estados de carga/vacío/éxito/error con el servidor y verificar que consultas públicas no exponen información administrativa.
