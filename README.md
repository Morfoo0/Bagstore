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
