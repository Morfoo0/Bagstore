# Bagstore — aplicación local integrada

Backend Python/FastAPI y PostgreSQL incluidos. Ver [inicio y acceso administrativo](backend/README.md). Ejecutar npm run dev:backend y npm run dev; abrir http://127.0.0.1:5173. npm run build permite también servir el frontend desde Python en puerto 8001. La cuenta administrativa se genera localmente, sin publicar su contraseña.

Validación: 52 pruebas frontend, 11 pruebas PostgreSQL/backend (incluyen recorrido HTTP/DOM completo), compilación y respaldo verificado. Pagos manuales y guías existentes; servicios comerciales externos y publicación no configurados. Entrega integrada en la rama independiente `proyecto-completo`. [Entrega vigente](docs/avance-11-backend-postgresql.md).

---

## Ejecutar desde una copia nueva (Windows)

Requiere Node.js, Python y PostgreSQL instalado; ver backend/README.md para la ruta de PostgreSQL.

```powershell
npm install
Copy-Item .env.example .env.local
npm run setup:backend
npm run build
npm run dev:backend
```

Abrir http://127.0.0.1:8001. Para desarrollo, ejecutar además npm run dev en otra terminal y usar el puerto 5173. La instalación genera una cuenta administrativa y su contraseña en un archivo privado local. No se distribuyen las contraseñas, fotos subidas ni datos de la base del autor; el esquema y el catálogo inicial están incluidos.

## Documentación histórica de frontend

> Estado vigente: **entrega 10 — frontend adaptado a API**. Copiar .env.example a .env.local y ejecutar Python en puerto 8000 junto a npm run dev. El modo api usa el catálogo del servidor y mantiene las escrituras bloqueadas hasta disponer de autenticación real. Para el prototipo independiente usar VITE_DATA_SOURCE=demo. No hay fallback automático a datos ficticios. Ver [adaptación](docs/avance-10-adaptacion-api.md) y [pendientes de backend](docs/pendientes-backend-integracion.md). Validación: npm test (52 pruebas), npm run build y npm run check:backend (requiere ambos servidores).

> Estado vigente: entrega 6. Panel y tienda comparten productos locales. Detalle, colecciones, inventario, reportes, reseñas, compartir, devoluciones y compra de prueba implementados. API real, sesión/roles y revisión visual nueva pendientes. Consultar docs/avance-06-recorridos-frontend.md y docs/contrato-api-propuesto.md. GitHub continúa pausado.

# Tienda de bolsas escolar

Carpeta independiente para la preparación del agente frontend en Codex.
Frontend escolar de tienda de bolsas, desarrollado con HTML, CSS y TypeScript. Vite se utiliza como herramienta de desarrollo y compilación, sin framework de interfaz.

Repositorio del equipo: https://github.com/Morfoo0/Bagstore

Rama propia acordada: `frontend-bafar`.

Documentación: https://app.notion.com/p/40d1a2cc445d814db5d1e32c432b6095

## Uso
Abrir esta carpeta como proyecto en Codex para que se apliquen las instrucciones de AGENTS.md.
Si ya existe un repositorio del equipo, llevar estas instrucciones a su checkout después de revisar y conservar cualquier AGENTS.md existente.

## Pendientes antes del desarrollo
- Publicar `frontend-bafar` directamente. Cada integrante trabaja con su propia base; la integración se hará al final y no requiere crear `main` ahora.
- Confirmar nombre de la tienda, identidad visual y contrato de API con el equipo.

Tecnologías acordadas: HTML, CSS y TypeScript para frontend; Python y PostgreSQL a cargo del equipo de backend.

## Ejecutar en Visual Studio Code

Abrir esta carpeta y ejecutar en su terminal:

```bash
npm install
npm run dev
```

Abrir la dirección local que imprime Vite. Para comprobar TypeScript y generar la versión de producción:

```bash
npm run build
```

## Primera versión

Inicio, encabezado, menú adaptable, colección, catálogo de ejemplo con búsqueda y filtros, carrito en página propia, preguntas frecuentes y pie de página. Los productos, precios e ilustraciones son ficticios. Los productos del carrito se guardan en este navegador. No hay compras, pagos ni autenticación reales.

El carrito incluye cantidades, eliminación, resumen, cupón BEIGE10 de prueba, opción de regalo y un botón Continuar compra que abre la revisión. La meta de envío de $1,000 es un ejemplo visual, no una promoción real; el envío definitivo no está calculado. El cupón y la marca de regalo se reinician al recargar.

El nombre Bagstore es provisional. Las fuentes se solicitan a Google Fonts, con fuentes del sistema como alternativa si no hay conexión.

Consultar docs/avance-01.md para el mapa de archivos, comprobaciones y pendientes.

## Acceso y vista previa administrativa

Mi cuenta abre #acceso. El formulario valida los campos pero informa que falta conectar la autenticación; no se envían ni guardan las credenciales. Para revisar la interfaz sin cuenta, usar Explorar panel de demostración.

El panel #admin permite navegar por las secciones y consultar productos/categorías ficticios. En #admin/productos se pueden crear, editar, desactivar y reactivar productos con guardado local exclusivo de esta demostración. Estos cambios no modifican todavía el catálogo público ni el carrito. No hay permisos reales ni operaciones administrativas conectadas a Python. Ver docs/avance-04-productos.md. Las pruebas de validación/repositorio se ejecutan con npm test (Node 24 usado en desarrollo).

## Colores y categorías

El color se elige de un catálogo con muestra de tono. Desde el formulario se puede agregar un color; se rechazan duplicados por mayúsculas, acentos y espacios. Categorías permite agregar tipos de bolsa y renombrarlos conservando su ID. Estas opciones aparecen en selectores y filtros públicos/administrativos. Los tonos del dibujo son decorativos y se configuran aparte del color para filtrar. Ver docs/avance-05-catalogos.md.

Las subidas a GitHub están pausadas por instrucción del usuario; los commits se conservan localmente.
