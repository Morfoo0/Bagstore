# Punto de continuidad — Bagstore

## Publicación autorizada

Estado: rama local proyecto-completo creada con toda la aplicación y guía de instalación. No se publicó aún. git push falló por acceso denegado al gestor de credenciales y la conexión GitHub rechazó crear el árbol con 403 Resource not accessible by integration. Se verificaron los 73 archivos rastreados sin datos privados ni claves. Para completar: autorizar escritura en la conexión o ejecutar git push -u origin proyecto-completo desde la terminal del usuario, dentro de esta carpeta. No se creó rama remota ni se alteraron main/backend/basededatos.

El usuario autorizó crear y subir la rama independiente proyecto-completo con la aplicación integrada. No tocar main ni backend. Esta instrucción sustituye la pausa histórica para esta entrega. La copia nueva requiere instalar dependencias y PostgreSQL; no requiere programar backend/frontend. Credenciales y datos locales excluidos.


## Preferencias vigentes

- Proyecto escolar independiente de tienda de bolsas. No mezclar con FitTrack.
- HTML, CSS y TypeScript con Vite; Python/PostgreSQL a cargo del equipo.
- Nombre provisional Bagstore y paleta Beige clásico.
- Cada integrante trabaja en su propia base y rama. Nuestra rama: frontend-bafar. No crear main para continuar.
- No ejecutar push ni publicar PR hasta nueva instrucción expresa del usuario. Se permiten commits locales.

## Estado vigente — entrega 11: backend completo local

Autorizado integrar backend y base sin operar en GitHub. Backend propio en backend/ (no modifica la copia del equipo), PostgreSQL privado en 127.0.0.1:55432, FastAPI en 8001. .env.local activa modo API integrado. Credenciales administrativas solo en backend/.runtime/ACCESO-LOCAL.txt, ignoradas por Git; no copiarlas a Notion.

Funciona: cuentas/sesiones/roles/CSRF, administración, colores, fotos, colecciones completas, inventario/historial, cotización, pedidos, reportes/ticket/CSV, seguimiento/guía, reseñas y devoluciones. Pagos se verifican manualmente y las guías son externas existentes; no hay pasarela ni reembolsos automáticos.

Validado: 52 pruebas frontend, 11 backend con PostgreSQL y recorrido DOM HTTP completo, compilación correcta y copia pg_dump verificada en .runtime/backups. No revisión visual integral ni impresión física. Los datos demo anteriores se conservan.

Para iniciar: npm run dev:backend y, en otra terminal, npm run dev. Frontend compilado disponible también desde http://127.0.0.1:8001 tras npm run build. Documentación: backend/README.md y docs/avance-11-backend-postgresql.md. Dependencias bloqueadas en backend/requirements.lock.txt. Para instalar desde cero: npm run setup:backend (requiere PostgreSQL instalado).

Procesos locales dejados activos: PostgreSQL privado, backend 8001 y frontend Vite 5173. GitHub sigue pausado. Pendientes externos: proveedor de pagos/tarjetas, etiquetas de paquetería, correo, políticas comerciales y despliegue público; ver límites en backend/README.md.

## Historial — entrega 10: API

Frontend adaptado al backend 5db5cc94dad8ec70c966bdc566d13754ab9278f2. .env.local activa VITE_DATA_SOURCE=api con proxy /api a Python en 8000. Catálogo, detalle, categorías y colecciones consultan servidor; carrito API independiente. Formularios y PUT preparados, guardado bloqueado sin sesión administrativa real. Edición de colecciones bloqueada hasta recibir membresía completa. Los módulos sin endpoints se identifican como pendientes; no se mezclan sus ejemplos con datos de API.

Validación: 52 pruebas y compilación correctas. npm run check:backend verificó Python real vía Vite: 8 productos activos, 3 categorías, 1 colección, detalle, filtros, paginación y render DOM sin errores. No prueba visual de navegador ni escrituras autorizadas reales.

Copia aislada de backend ejecutándose para revisión local: C:/Users/bafar/Documents/Codex/2026-11-03/new-chat/outputs/backend-integration-check-5db5cc9. Iniciar desde allí con .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 si se detiene. Sus datos son temporales. No se modificó su código ni se fusionaron ramas.

Consultar docs/avance-10-adaptacion-api.md y docs/pendientes-backend-integracion.md. Para volver al prototipo local cambiar VITE_DATA_SOURCE=demo en .env.local y reiniciar Vite. Mantener GitHub pausado.

## Historial — entrega 9

Reportes tiene Detalles por pedido y ticket de preparación imprimible, con productos históricos, cantidades, color si se registró, importes y revisión de paquete. Referencia local de paquetería/guía existente por pedido. No genera etiqueta oficial ni contiene domicilio en pedidos locales. Consultar docs/avance-09-detalles-ticket.md. Validación: 39 pruebas y compilación correctas; impresión física/PDF pendiente. Se mantiene la cuenta obligatoria y la dependencia de API.

## Historial — entrega 8

Cuenta obligatoria para continuar la compra. Registro en #registro, acceso desde carrito y guardas de rutas de compra implementadas. El carrito se conserva. Sin API de cuentas, la compra queda detenida en acceso; no se simula sesión. El retorno tras autenticación real debe conectarse con Python. Consultar docs/avance-08-registro-acceso-compra.md. Validación actual: 37 pruebas y compilación correctas.

## Historial — entrega 7

Textos de tienda y panel revisados: consultar docs/avance-07-textos-tienda.md. Se retiró la meta ficticia de envío, se aclararon totales y acciones del carrito, y se mantuvieron avisos de vista previa/sin cobros. 35 pruebas y compilación correctas. La integración real continúa pendiente.

Consultar docs/avance-06-recorridos-frontend.md y docs/contrato-api-propuesto.md.

- Productos activos del panel y tienda unificados, incluyendo fotos y catálogos por ID.
- Detalle, reseñas, compartir, colecciones, inventario, reportes CSV y devoluciones implementados con persistencia local.
- Recorrido de compra de demostración con entrega/pago/confirmación; genera pedido ficticio y descuenta stock local.
- Inventario inicial: 20 unidades ficticias por producto. No existen ventas de ejemplo precargadas.
- Portafolio de colecciones implementado como propuesta pendiente de confirmar con escuela/equipo.
- Cliente fetch y comprobación de salud configurables. Sesión, roles y recursos reales todavía sin conectar.
- npm test: 35 pruebas correctas. npm run build: correcto. Pruebas DOM con jsdom; revisión visual nueva pendiente en navegador real.

## Retomar

1. npm run dev y revisar #catalogo, #producto/1, #admin/colecciones, #admin/existencias, #admin/reportes y #devoluciones.
2. Probar compra local con un producto activo. No ingresar datos personales/bancarios reales.
3. Revisar visualmente móvil/escritorio, teclado y carga real de fotos. Corregir cualquier problema observado.
4. Acordar API con Python antes de sustituir repositorios locales. Confirmar contenido y significado de portafolios.
5. Mantener Notion al día y NO publicar en GitHub hasta instrucción expresa.

## Historial anterior (sustituido por entrega 6)

## Estado actual

- Inicio, encabezado, pie, menú móvil, navegación y ayuda iniciales.
- Catálogo público de cuatro bolsas de ejemplo, búsqueda y filtros de tipo/color.
- Carrito en página propia, cantidades, eliminación, cupón de prueba, regalo y revisión; sin pedidos ni pagos reales.
- Acceso visual validado; no envía ni guarda credenciales ni concede sesión real.
- Panel: productos con alta/edición, foto opcional, desactivar/reactivar, búsqueda/filtros y persistencia local.
- Colores compartidos con IDs, básicos iniciales, muestra y alta desde el formulario, evitando duplicados.
- Categorías configurables con alta/renombrado e IDs estables. Opciones compartidas en selectores/filtros.
- Catálogos y productos anteriores conservados mediante vinculación a IDs. Caramelo/Cacao se agrupan en Café; Arena/Lino/Beige clásico en Beige.

Los productos del panel y los cuatro productos públicos todavía son conjuntos de demostración independientes. Los catálogos de colores/categorías sí se comparten en este navegador. No afirmar que el panel modifica una base de datos ni que existe autenticación real.

## Validación más reciente

npm run build correcto y 17 pruebas aprobadas. IDs/referencias HTML comprobados. Servidor local respondió HTTP 200. Falta revisión visual/interactiva de las últimas entregas: el único destino de control de aplicaciones disponible fue Codex, cuya interfaz no se automatiza.

## Qué sigue

1. Revisar en navegador colores, alta integrada, categorías nuevas/renombradas, productos anteriores, filtros, foto y modales anidados; verificar teclado y móvil.
2. Gestión de colecciones y existencias, después reportes de ventas.
3. Detalle de producto, reseñas, compartir y devoluciones; aclarar definición académica de portafolios.
4. Acordar contratos de Python: categorías/colores/productos, roles/sesión, errores, stock, cupones/envíos, pedidos y pagos. Integrar fetch y comprobar permisos reales.

## Retomar

Abrir la raíz tienda-bolsas-escolar en VS Code. Ejecutar npm run dev si la vista está detenida, npm test para pruebas y npm run build para compilar.
Rutas: #acceso, #admin, #admin/productos, #admin/categorias, #carrito y #checkout.

Leer AGENTS.md y docs/avance-05-catalogos.md. Notion: https://www.notion.so/40d1a2cc445d814db5d1e32c432b6095

Todo se guarda localmente. Revisar git status al retomar sin subir a GitHub. El servidor temporal puede detenerse entre sesiones; los archivos fuente y commits permanecen guardados.
