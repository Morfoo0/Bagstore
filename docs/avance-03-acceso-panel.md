# Entrega 3 — Acceso y estructura administrativa

## Implementado

- Ruta #acceso enlazada desde Mi cuenta, con correo y contraseña obligatorios, validación HTML de correo y control mostrar/ocultar contraseña.
- Estados de envío y aviso accesible de que la autenticación aún no está configurada. No concede sesión ni rol.
- Credenciales sin envío, registro ni persistencia. El campo contraseña se limpia al enviar o salir de la pantalla.
- Entrada explícita a la vista previa del panel, separada del inicio de sesión.
- Panel #admin con navegación a resumen, productos, categorías, colecciones, existencias y reportes, indicando la sección activa.
- Resumen con conteos derivados de datos ficticios; tabla de cuatro productos de consulta y tres categorías de ejemplo.
- Colecciones, existencias y reportes muestran estados pendientes, sin métricas ni stock inventados.
- Regreso a la tienda y salida de la vista previa hacia acceso.

## Archivos para revisar en VS Code

| Archivo | Responsabilidad |
| --- | --- |
| index.html | Formulario y estructura de las vistas administrativas |
| src/access.css | Distribución, paleta y adaptación a móvil |
| src/components/access.ts | Navegación del panel, formulario y datos de demostración |
| src/services/auth.ts | Contrato provisional y rechazo explícito de autenticación no configurada |
| src/components/cart.ts | Coordinación de visibilidad entre carrito y nuevas vistas |
| src/main.ts | Inicialización del módulo de acceso |

## Verificación

- npm run build: TypeScript y Vite correctos.
- Formulario vacío: navegador exige correo obligatorio.
- Envío con datos ficticios: aviso de API pendiente, sin acceso autenticado; contraseña limpiada.
- Navegación acceso → panel → productos → tienda: comprobada en navegador.
- Tabla muestra cuatro productos ficticios y resumen tres categorías.
- Diseño revisado a 1440 y 390 px; se corrigió ancho mínimo de la cuadrícula administrativa. Sin desbordamiento horizontal de la página en resumen y productos móviles; la tabla y menú permiten desplazamiento interno.
- Consola sin errores en los flujos comprobados.

## Pendientes

Autenticación real y permisos definidos por Python; operaciones de alta, edición y eliminación/desactivación; gestión de categorías, colecciones y existencias; reportes de ventas y consumo de API. La vista previa es pública y contiene únicamente datos de ejemplo: no constituye protección de rutas ni implementación de roles.

No se agregaron registro ni recuperación de contraseña: requieren confirmar alcance y contrato con el equipo.
