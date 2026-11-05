export class ApiError extends Error {
  status: number; code?: string; details: { campo: string; mensaje: string }[];
  constructor(message: string, status = 0, code?: string, details: { campo: string; mensaje: string }[] = []) { super(message); this.name = 'ApiError'; this.status = status; this.code = code; this.details = details; }
}
let csrfToken: string | undefined;
export function setCsrfToken(value?: string) { csrfToken = value; }
export class ApiClient {
  baseUrl: string;
  private fetcher: typeof fetch;
  constructor(baseUrl: string, fetcher: typeof fetch = fetch) {
    const url = new URL(baseUrl);
    if (!['http:', 'https:'].includes(url.protocol)) throw new ApiError('La URL de API debe usar HTTP o HTTPS.');
    this.baseUrl = url.href.replace(/\/$/, ''); this.fetcher = fetcher;
  }
  async request<T>(path: string, options: RequestInit = {}, timeoutMs = 10000): Promise<T> {
    if (!path.startsWith('/') || path.startsWith('//') || path.includes('://')) throw new ApiError('La ruta de API debe ser relativa al servidor configurado.');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const headers = new Headers(options.headers); headers.set('Accept', 'application/json');
      if (csrfToken && options.method && !['GET','HEAD','OPTIONS'].includes(options.method.toUpperCase())) headers.set('X-CSRF-Token',csrfToken);
      if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
      const response = await this.fetcher(`${this.baseUrl}${path}`, { ...options, headers, signal: controller.signal, credentials: 'include' });
      if (response.status === 204) return undefined as T;
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        const body = data?.error;
        const details = Array.isArray(body?.detalles) ? body.detalles.filter((d: unknown): d is {campo: string; mensaje: string} => !!d && typeof d === 'object' && typeof (d as {campo?: unknown}).campo === 'string' && typeof (d as {mensaje?: unknown}).mensaje === 'string') : [];
        const fallback = response.status === 401 ? 'Tu sesión no está disponible. Inicia sesión nuevamente.' : response.status === 403 ? 'No tienes permiso para esta operación.' : `El servidor respondió con un error (${response.status}).`;
        throw new ApiError(response.status >= 500 ? fallback : typeof body?.mensaje === 'string' ? body.mensaje : fallback, response.status, typeof body?.codigo === 'string' ? body.codigo : undefined, details);
      }
      if (data === null) throw new ApiError('El servidor no devolvió una respuesta JSON válida.', response.status);
      return data as T;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(controller.signal.aborted ? 'El servidor tardó demasiado. Inténtalo de nuevo.' : 'No se pudo conectar con el servidor. Revisa la conexión y CORS.');
    } finally { clearTimeout(timer); }
  }
}
export interface BackendRoutes { products?: string; collections?: string; stock?: string; reviews?: string; orders?: string; returns?: string; login?: string; session?: string; health?: string; }
/** Rutas suministradas por el equipo, nunca inferidas. El consumidor valida su respuesta. */
export function backendResource(client: ApiClient, routes: BackendRoutes, resource: keyof BackendRoutes) {
  function path() { if (!routes[resource]) throw new ApiError(`Falta acordar/configurar la ruta de ${resource}.`); return routes[resource]!; }
  return { list: <T>() => client.request<T>(path()), get: <T>(id: string | number) => client.request<T>(`${path()}/${encodeURIComponent(id)}`), create: <T>(payload: unknown) => client.request<T>(path(), { method: 'POST', body: JSON.stringify(payload) }), update: <T>(id: string | number, payload: unknown) => client.request<T>(`${path().replace(/\/$/, '')}/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(payload) }), remove: (id: string | number) => client.request<void>(`${path()}/${encodeURIComponent(id)}`, {method: 'DELETE'}) };
}
