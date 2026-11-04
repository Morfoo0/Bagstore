/** Contrato provisional del frontend; acordar sesión, roles y errores con Python. */
export interface Credentials {
  email: string;
  password: string;
}

export class AuthNotConfiguredError extends Error {
  constructor() {
    super('El inicio de sesión aún no está disponible. Inténtalo más tarde o vuelve a explorar la tienda.');
    this.name = 'AuthNotConfiguredError';
  }
}

/** No envía ni persiste credenciales. No concede una sesión ni un rol. */
export async function signIn(_credentials: Credentials): Promise<never> {
  throw new AuthNotConfiguredError();
}

export interface Registration extends Credentials { name: string; }
export async function signUp(_registration: Registration): Promise<never> {
  throw new AuthNotConfiguredError();
}

/** Sin contrato de sesión no se concede acceso. Nunca confiar en un indicador de localStorage. */
export function hasCustomerSession(): boolean { return false; }
const PURCHASE_INTENT = 'bagstore.purchase-intent';
export function purchaseDestination(): string | null {
  try { return sessionStorage.getItem(PURCHASE_INTENT) === '#compra/entrega' ? '#compra/entrega' : null; }
  catch { return null; }
}
export function requireCustomerAccess(): boolean {
  if (hasCustomerSession()) return true;
  try { sessionStorage.setItem(PURCHASE_INTENT, '#compra/entrega'); } catch { /* El carrito persiste independientemente. */ }
  location.hash = 'acceso';
  return false;
}
