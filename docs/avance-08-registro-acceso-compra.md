# Entrega 8 — Cuenta necesaria para comprar

Decisión confirmada por el usuario: se puede explorar y preparar el carrito sin cuenta, pero para continuar la compra se requiere inicio de sesión o registro.

Implementado: ruta #registro con nombre, correo, contraseña y confirmación; validación HTML y coincidencia de contraseñas; mostrar/ocultar contraseña, carga y errores. Los secretos se limpian al enviar o cambiar de ruta y no se persisten ni envían con el servicio actual.

Continuar con mi compra redirige a acceso, conserva el carrito y ofrece Crear cuenta. Las rutas directas #compra/entrega, #compra/pago y #compra/confirmacion y el envío de pedido requieren sesión. Se guarda exclusivamente un destino permitido (#compra/entrega) en sessionStorage, sin datos personales ni URLs externas.

Límite actual: auth.ts no concede sesión y signIn/signUp informan indisponibilidad. Por tanto, el recorrido público queda detenido en acceso hasta conectar la API. Ya no puede finalizarse una compra local desde la interfaz sin cuenta. Las reglas de pedidos locales siguen verificadas en pruebas de servicio.

Pendiente con Python: registro, sesión verificada y asociación de pedidos al usuario; tras autenticar, consumir/limpiar el destino guardado y reanudar entrega. La continuación automática después de autenticación real no está implementada, pues aún no hay respuesta de sesión acordada. El servidor debe exigir sesión, verificar pertenencia del pedido y rechazar operaciones no autorizadas. La guarda del frontend no sustituye esa autorización.

Validación: 37 pruebas aprobadas y npm run build correcto. Pruebas de interacción cubren carrito conservado, registro inválido/API indisponible y rutas directas bloqueadas. Revisión visual pendiente. GitHub pausado.
