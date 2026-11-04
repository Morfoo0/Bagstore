# Entrega 4 — Gestión de productos de demostración

## Preferencia vigente

El usuario pausó todas las subidas a GitHub hasta nueva indicación expresa. Se continúa con archivos y commits locales, sin push ni PR.

## Implementado

- Botón Nuevo producto y formulario modal con nombre, categoría, precio MXN, nombre de color y tonos de ilustración.
- Validación por campo: longitudes, categoría admitida, color hexadecimal y precio positivo con máximo dos decimales y límite de prueba de $999,999.99.
- Vista previa de ilustración y nombre en escritorio.
- Edición precargada conservando ID y estado del producto.
- Desactivar/reactivar con confirmación, sin borrar datos.
- Aviso para descartar cambios del formulario.
- Búsqueda por nombre, color y referencia; filtros todos/activos/inactivos y estado sin resultados.
- Guardado local exclusivo del panel en bagstore.admin-products.v1, con validación de datos recuperados y aviso si falla el almacenamiento.
- El catálogo público y el carrito siguen utilizando sus propios ejemplos originales. No se sincronizan con esta demostración administrativa; la integración se hará mediante el contrato del equipo.
- Datos de texto del formulario escapados antes de construir la tabla; tonos y categorías validados.

## Archivos

src/components/product-manager.ts: formularios, modales, tabla y filtros.
src/services/admin-products.ts: validación y repositorio local de demostración.
src/products.css: estilos del formulario y acciones.
tests/admin-products.test.ts: pruebas del repositorio y reglas de validación.

## Verificación realizada

- npm run build: TypeScript y Vite correctos.
- Siete pruebas pasaron: precios/campos inválidos, creación/persistencia, edición y reactivación, IDs desconocidos, almacenamiento corrupto/duplicado, fallo de guardado y aislamiento de copias.
- HTML: IDs únicos y referencias estáticas/dinámicas del módulo presentes.
- Vite inició en http://127.0.0.1:5173/ y se solicitó mostrar #admin/productos en el navegador de la app.
- Pendiente revisión interactiva y visual: en esta sesión no hubo navegador externo controlable. La consulta HTTP local fue bloqueada por permisos de socket. No afirmar que se verificaron los clics, el foco o la vista móvil de esta entrega.

## Siguiente paso

Revisar Nuevo producto, validación, guardar, editar, cancelar con cambios, desactivar, reactivar y recargar; comprobar móvil y teclado. Después implementar gestión de categorías y colecciones.

Campos definitivos, categorías configurables, fotografías, permisos reales, API y diferencia entre eliminación y desactivación siguen por acordar con el equipo. No se añadió eliminación definitiva.
