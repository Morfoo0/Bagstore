# Backend integrado de Bagstore

Implementación local FastAPI/PostgreSQL, compatible con el catálogo previo del equipo y extendida para cuentas, pedidos y administración. El código de la copia de la rama backend del equipo se conserva sin cambios; no se fusionaron ramas ni se hicieron operaciones remotas en GitHub.

## Ejecutar en esta computadora

Requisitos: Node/npm, Python y PostgreSQL instalado. En esta copia ya están preparados el entorno y una base privada del proyecto en `127.0.0.1:55432`, independiente de cualquier servicio existente.

Desde la raíz del proyecto:

```powershell
npm run dev:backend
```

En otra terminal:

```powershell
npm run dev
```

- Frontend de desarrollo: http://127.0.0.1:5173
- Backend y frontend compilado: http://127.0.0.1:8001 (requiere `npm run build`)
- Documentación API: http://127.0.0.1:8001/docs
- Salud y base: http://127.0.0.1:8001/api/health

No iniciar dos backends simultáneamente en 8001. Si los procesos se detuvieron, `npm run dev:backend` vuelve a conectar/iniciar la base privada. El lanzador comprueba que la base sea la del proyecto antes de operar. No usar `initdb` sobre una carpeta de datos existente ni borrar archivos de PostgreSQL.

## Cuenta administrativa

El primer arranque genera una contraseña aleatoria. Consultarla exclusivamente en `backend/.runtime/ACCESO-LOCAL.txt`. No publicarla en Notion ni GitHub. Las cuentas creadas desde registro siempre tienen rol cliente; una petición no puede asignarse permisos administrativos.

El archivo de credenciales, la configuración de conexión, la base, las fotografías y el entorno virtual están excluidos de Git. Guardar el código no sustituye respaldar los datos.

## Primera instalación en otra computadora Windows

1. Instalar PostgreSQL y Python (probado con Python 3.13). Si PostgreSQL no está en `C:/Program Files/PostgreSQL/18/bin`, establecer `POSTGRES_BIN` con su carpeta bin.
2. Ejecutar `npm install` y copiar `.env.example` a `.env.local`.
3. Ejecutar `npm run setup:backend`. Crea `.venv`, instala `requirements.lock.txt`, genera secretos locales y crea exclusivamente la base privada.
4. Ejecutar `npm run dev:backend` y `npm run dev` en terminales separadas.

Para una instalación PostgreSQL administrada externamente se puede suministrar `DATABASE_URL` y `BAGSTORE_ADMIN_EMAIL`/`BAGSTORE_ADMIN_PASSWORD` al proceso Python; iniciar Uvicorn directamente en lugar del bootstrap Windows. Nunca colocar secretos en variables `VITE_`.

## Datos y contrato

`schema.sql` crea tablas relacionales con claves foráneas, índices, restricciones, importes decimales y versión inicial de esquema. No almacena el catálogo como un arreglo de memoria. El catálogo inicial contiene cuatro bolsas y diez colores y se crea solo si aún no hay categorías.

Incluye catálogo con IDs numéricos, colores normalizados, colección con membresía administrativa completa, fotos JPEG en disco, ajustes de inventario/historial, pedidos con líneas históricas, cotización, pagos manuales, seguimiento de envío, reseñas y devoluciones. La API valida permisos y propietario, calcula precios/descuentos/envío y bloquea filas para descontar stock. Reintentar un pedido con la misma clave no duplica sus líneas ni su stock.

Sesiones aleatorias con cookie HttpOnly, SameSite Strict, expiración y CSRF; contraseñas PBKDF2 con sal. Los pedidos y sesiones persisten en PostgreSQL. El frontend guarda únicamente el carrito en el navegador, sin credenciales ni roles persistidos allí.

## Validación

```powershell
npm test
npm run test:backend
npm run build
npm run check:backend
```

Se aprobaron 52 pruebas TypeScript/DOM y 11 pruebas del backend, incluyendo un recorrido DOM con HTTP real y PostgreSQL en una base de pruebas independiente. La prueba de última unidad usa dos compradores concurrentes. La suite crea y elimina una base `bagstore_test_<aleatorio>` y no vacía la base del usuario. Las pruebas no equivalen a revisión visual de navegador ni a impresión física.

## Respaldar

```powershell
backend/.venv/Scripts/python.exe backend/backup.py
```

Genera y verifica un archivo de respaldo en `backend/.runtime/backups/`. Respaldar también `backend/uploads` y guardar la configuración de conexión en un lugar privado. No subirlos al repositorio. Las restauraciones deben hacerse en un destino elegido y comprobado, no ejecutarse automáticamente sobre una base con datos.

## Límites comerciales y despliegue

- Transferencia o efectivo al recoger; estado inicial de pago pendiente. El administrador confirma manualmente haber recibido el dinero. No se procesan tarjetas, no hay pasarela de pagos ni webhooks.
- La guía se registra desde una paquetería existente; el ticket sirve para preparación y no es factura ni etiqueta oficial. Actualmente hay una referencia por pedido, sin paquetes parciales.
- Devoluciones registran/gestionan solicitudes; cerrar una no reembolsa dinero ni repone stock automáticamente. Esas operaciones deben acordarse y verificarse con la tienda antes de automatizarlas.
- Tarifa local configurable con `SHIPPING_PRICE` (inicialmente 79 MXN); `BEIGE10` conserva el cupón escolar de ejemplo. Definir políticas, condiciones y promociones comerciales antes de vender.
- No incluye recuperación/verificación de correo, facturación fiscal, envío de mensajes o notificaciones SMTP.
- Reportes listan hasta 500 pedidos recientes; inventario, 500 productos y 100 movimientos. Para mayor volumen ampliar paginación/reportes.
- La instancia privada se liga a loopback. Antes de publicar: HTTPS, `COOKIE_SECURE=1`, `PUBLIC_ORIGIN`, base de datos y archivos con respaldos administrados, proveedor de pago/paquetería si se necesitan, supervisión de procesos y revisión de seguridad/despliegue. No desplegado públicamente.
