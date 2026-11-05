# Entrega 11 — Aplicación local con backend y PostgreSQL

Autorización: el usuario amplió el trabajo para incluir el backend y la base. Conserva la prohibición de operar en GitHub; todo se realizó localmente en frontend-bafar. La copia del backend del equipo no se modificó ni fusionó; se reutilizó su contrato de catálogo como base de compatibilidad.

## Entregado

- Backend propio en backend/server.py y esquema relacional PostgreSQL en backend/schema.sql.
- PostgreSQL privado del proyecto, puerto 55432; API 8001. Datos y credenciales fuera de Git. El servicio HTTP puede servir la compilación de frontend además de API.
- Registro/login/logout, sesión persistida, cliente/administrador, contraseñas con sal, cookies HttpOnly y CSRF. Autorización y pertenencia comprobadas por servidor.
- Catálogo/categorías/colores/colecciones con escrituras reales, consulta de inactivos y membresía completa. Fotos verificadas/recodificadas y almacenadas en servidor.
- Inventario con ajustes y movimientos. Cotización y pedido con importes de servidor, líneas históricas, clave para reintentos y descuento atómico de existencias.
- Pedidos del cliente; reportes administrativos con pagos pendientes/confirmados separados, filtros, CSV, detalle/ticket imprimible, estado de preparación/entrega y guía existente.
- Reseñas persistidas por cliente/producto y solicitudes de devolución de productos entregados, con gestión administrativa.
- Frontend conectado mediante VITE_INTEGRATED_BACKEND=1 y proxy 8001. El modo demo conserva sus datos anteriores; no fueron borrados ni importados automáticamente.

## Verificado

52 pruebas del frontend aprobadas y TypeScript/Vite correctos. 11 pruebas backend/PostgreSQL aprobadas: permisos, CSRF, colores duplicados, inactivos, membresía, dependencias, totales decimales, reintentos, propiedad, stock concurrente, pago manual/entrega, devoluciones, reseñas, fotos, domicilio/guía y datos persistentes.

El recorrido de frontend se ejecutó con jsdom, fetch HTTP real y un servidor contra una base de pruebas temporal: registro → acceso → carrito → cotización/cupón → pedido → ticket → reportes → pago manual → entrega → ajuste de inventario → devolución → reseña, sin errores DOM. No se crearon estos pedidos de prueba en la base del usuario. Revisión visual completa e impresión física siguen pendientes.

Se corrigió el arranque de PostgreSQL en Windows para comprobar la conexión antes de iniciar otro proceso. En este entorno la consulta de procesos no era fiable; no se usa para decidir si la base está activa. Tras corregirlo se repitió y aprobó la suite.

## Uso y límites

Consultar backend/README.md. Cuenta administrativa local generada en backend/.runtime/ACCESO-LOCAL.txt; no copiar a Notion. Pagos y guías se verifican/registran manualmente: no hay cobro con tarjetas, etiquetas oficiales ni reembolsos automáticos. Correo, pasarelas, paqueterías y despliegue público necesitan configuración externa y decisiones de negocio. Esta entrega es una aplicación escolar local funcional, no una tienda ya publicada comercialmente.

GitHub permanece intacto. No se realizaron push, PR ni merges.
