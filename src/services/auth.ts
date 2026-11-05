import { ApiClient, setCsrfToken } from './api';
export interface SessionUser { id: number; name: string; email: string; role: 'cliente'|'administrador'; }
let client: ApiClient | undefined;
let user: SessionUser | null = null;
function accept(data: {user: SessionUser|null; csrf: string|null}) {
  if (data.user && (!Number.isInteger(data.user.id) || !['cliente','administrador'].includes(data.user.role) || typeof data.csrf !== 'string')) throw Error('Respuesta de sesión inválida.');
  user=data.user;setCsrfToken(data.csrf || undefined);
  window.dispatchEvent(new Event('bagstore-session-changed'));
  return user;
}
export async function configureAuth(baseUrl: string) { client=new ApiClient(baseUrl); return refreshSession(); }
export async function refreshSession() { return client ? accept(await client.request('/api/auth/session')) : null; }
export function currentUser() { return user; }
export function isAdministrator() { return user?.role==='administrador'; }
export async function signOut() { if(client)await client.request('/api/auth/logout',{method:'POST'});user=null;setCsrfToken();window.dispatchEvent(new Event('bagstore-session-changed')); }
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
export async function signIn(credentials: Credentials) {
  if (!client) throw new AuthNotConfiguredError();
  return accept(await client.request('/api/auth/login',{method:'POST',body:JSON.stringify(credentials)}));
}

export interface Registration extends Credentials { name: string; }
export async function signUp(registration: Registration) {
  if (!client) throw new AuthNotConfiguredError();
  return accept(await client.request('/api/auth/register',{method:'POST',body:JSON.stringify(registration)}));
}

/** Sin contrato de sesión no se concede acceso. Nunca confiar en un indicador de localStorage. */
export function hasCustomerSession(): boolean { return user!==null; }
const PURCHASE_INTENT = 'bagstore.purchase-intent';
export function purchaseDestination(): string | null {
  try { return sessionStorage.getItem(PURCHASE_INTENT) === '#compra/entrega' ? '#compra/entrega' : null; }
  catch { return null; }
}
export function consumePurchaseDestination() { const destination=purchaseDestination();try{sessionStorage.removeItem(PURCHASE_INTENT);}catch{}return destination; }
export function requireCustomerAccess(): boolean {
  if (hasCustomerSession()) return true;
  try { sessionStorage.setItem(PURCHASE_INTENT, '#compra/entrega'); } catch { /* El carrito persiste independientemente. */ }
  location.hash = 'acceso';
  return false;
}
