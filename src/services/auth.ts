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
