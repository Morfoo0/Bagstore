# Entrega 10 — Adaptación al backend disponible

## Implementado

- Modo API separado de demostración mediante VITE_DATA_SOURCE=api o demo. Los productos, stock y carritos no se mezclan. Los datos antiguos se conservan sin migración automática.
- /api/productos, detalle, /api/categorias, /api/colecciones y /api/health, con validación de respuestas JSON en ejecución, IDs numéricos y envoltura datos/paginacion.
- Catálogo público: búsqueda, categorías del servidor, filtros por colección, paginación y orden. Conserva agotados activos y usa disponible/existencias; ya no asigna 20 unidades en modo API.
- Detalle: SKU, descripción, precio, stock y galería HTTP(S). Agregar al carrito vuelve a consultar el detalle; errores de red al restaurar no borran el carrito API. Las URLs inválidas se rechazan.
- Formularios preparados para nombre, SKU obligatorio/inmutable, descripción, precio, categoría, existencias, estado y hasta 10 imágenes por URL con orden, texto alternativo y principal. Categorías: nombre/descripcion/orden/estado; colecciones: nombre/descripcion/portada/estado y selección de productos.
- Operaciones de servicio POST/PUT completos y DELETE con 204. PUT no envía SKU editable ni colores/data URLs/campos de ilustración. Conserva el arreglo completo de imágenes y el estado.
- Errores error.codigo/mensaje/detalles por campo, validación local, cargas y reintentos. No anuncia éxito si el servidor rechaza una operación.
- Proxy /api en desarrollo a Python (puerto 8000), evitando la diferencia localhost/127.0.0.1. En producción se configura proxy o CORS.

## Límites explícitos

La API actual no autentica: el proveedor de sesión administrativa devuelve false por defecto. Se pueden abrir/preparar formularios y consultar activos, pero no guardar ni ajustar stock desde la interfaz hasta integrar permisos verificados. No se aprovecha el no-op del backend para habilitar escrituras públicas. La implementación de envío PUT y errores se verifica con un proveedor administrativo simulado únicamente en pruebas.

Edición de colecciones bloqueada: falta recuperar producto_ids administrativos completos; no se infiere la membresía de un listado público incompleto. Las nuevas colecciones ofrecen selección por nombre, no edición manual de IDs.

Colores y subida de fotos requieren endpoints nuevos. Login/registro/compra siguen detenidos sin sesión. Reportes/ticket, reseñas y devoluciones del prototipo permanecen en modo demo; en modo API aparecen como servicios pendientes, sin mostrar datos locales como si fueran del servidor.

## Ejecutar

1. Copiar .env.example a .env.local. Ya existe configuración local API en esta copia del usuario; está ignorada por Git.
2. Iniciar Python en el repositorio del equipo: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000.
3. En frontend: npm run dev. El proxy usa API_PROXY_TARGET; por defecto http://127.0.0.1:8000. VITE_API_BASE_URL vacío utiliza el mismo origen del navegador; para servidor externo indicar URL raíz, sin /api final.
4. Para revisar el prototipo sin backend: VITE_DATA_SOURCE=demo y reiniciar Vite. No se aplica fallback automático si la API falla.

## Validación

npm test: 52 pruebas correctas (39 previas y 13 de adaptación API/DOM). npm run build: TypeScript/Vite correctos. Las pruebas cubren respuestas reales del contrato reproducidas con fetch simulado, PUT y campos permitidos, errores 409/422, imágenes, stock, filtros, carrito y bloqueo de acceso. No equivalen a revisión visual de navegador.

Lista para el equipo: docs/pendientes-backend-integracion.md. GitHub sigue pausado; no se fusionaron ramas ni se modificó el backend del equipo.

### Comprobación contra Python real

Se clonó la rama backend en una carpeta aislada de integración (backend-integration-check-5db5cc9), sin modificar su código ni mezclar ramas. Dependencias instaladas en su .venv. Servidor local iniciado en 127.0.0.1:8000 y dejado en ejecución para revisar el frontend. No se publicaron datos ni se enviaron escrituras.

npm run check:backend aprobó salud, validación de detalle, filtros de categoría, orden y página 2 a través de http://127.0.0.1:5173/api; devolvió 8 productos activos, 3 categorías y 1 colección. El componente renderizó 8 productos en jsdom con fetch HTTP real, sin errores DOM. Esta prueba no sustituye la revisión visual ni prueba permisos reales. Al inicio se corrigió el adaptador de prueba para usar el AbortController de Node junto a su fetch; no fue un defecto del navegador.
