# Entrega 7 — Textos de la tienda

Se revisaron los textos de inicio, catálogo, detalle, carrito, revisión, entrega, pago, confirmación, acceso, colecciones/portafolio, reseñas, devoluciones y panel administrativo.

- Tono comercial uniforme, acciones claras y mensajes de error orientados a resolver el problema.
- Carrito: «Continuar con mi compra», «Total antes del envío», cupón y regalo con instrucciones breves. Se retiró la meta ficticia de envío de $1,000; no existe una promoción acordada.
- Revisión: el texto de entrega/pago ya dirige al siguiente paso; se eliminó el aviso obsoleto de integración pendiente.
- Inicio/pie: identidad de Bagstore, sin explicar tecnologías ni tareas escolares en el recorrido público. Se retiró el símbolo de marca registrada, cuyo registro no está confirmado.
- Administración: títulos y botones operativos, notificaciones de guardado, y resumen con accesos a productos, inventario y reportes en lugar de una lista de desarrollo.
- La vista previa se identifica en el encabezado. Acceso, pago y confirmación conservan avisos explícitos de indisponibilidad o ausencia de cobros/envíos. El panel conserva el aviso de almacenamiento local y stock ficticio; la sección de conexión mantiene las instrucciones técnicas correspondientes.
- No se inventaron políticas de devolución, promociones, garantías, especificaciones de productos ni una sesión real. No se conectó una API por cambiar los textos.
- Se conserva el producto de prueba solicitado y los datos previos del usuario. Las etiquetas internas de métodos de pago/entrega siguen compatibles con los pedidos locales; se presentan con nombres legibles en la confirmación.

Validación ejecutada: npm test (35 pruebas correctas), npm run build (TypeScript y Vite correctos) y git diff --check sin errores. Se ajustó la comprobación de confirmación al nuevo título; no se agregaron pruebas que solo repliquen textos. La revisión visual integral de pantallas nuevas sigue pendiente.

GitHub permanece pausado. Cambios exclusivos del frontend y documentación local/Notion.
