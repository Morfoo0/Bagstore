import type { CatalogRepository } from '../services/catalogs';
import { products } from '../data/products';
import { setupProductManager } from './product-manager';
import { AuthNotConfiguredError, signIn, signUp, purchaseDestination } from '../services/auth';

function node<T extends HTMLElement = HTMLElement>(selector: string): T {
  const result = document.querySelector<T>(selector);
  if (!result) throw new Error(`Elemento de acceso no encontrado: ${selector}`);
  return result;
}

const sections = {
  resumen: { title: 'Todo empieza con una buena base.', subtitle: 'Un vistazo al espacio de trabajo de Bagstore.' },
  productos: { title: 'Tus productos.', subtitle: 'Crea, edita y organiza los productos de tu catálogo.' },
  categorias: { title: 'Un lugar para cada estilo.', subtitle: 'Agrega y renombra tipos de bolsa para seleccionarlos en tus productos.' },
  colecciones: { title: 'Colecciones con personalidad.', subtitle: 'Agrupa tus productos y presenta cada colección a tu manera.' },
  existencias: { title: 'Cada bolsa cuenta.', subtitle: 'Consulta existencias y registra ajustes de inventario.' },
  reportes: { title: 'Conoce tus resultados.', subtitle: 'Consulta tus pedidos, filtra por fechas y exporta los resultados.' },
  devoluciones: { title: 'Acompaña cada solicitud.', subtitle: 'Revisa solicitudes y mantén actualizado su estado.' },
  conexion: { title: 'Conectemos las piezas.', subtitle: 'Cliente HTTP preparado; contratos y servidor pendientes del equipo.' }
};
type AdminSection = keyof typeof sections;

export function setupAccess(catalogs: CatalogRepository): void {
  const form = node<HTMLFormElement>('#access-form');
  const password = node<HTMLInputElement>('#access-password');
  const feedback = node('#access-feedback');
  const toggle = node<HTMLButtonElement>('#password-toggle');
  toggle.addEventListener('click', () => {
    const reveal = password.type === 'password';
    password.type = reveal ? 'text' : 'password';
    toggle.textContent = reveal ? 'Ocultar' : 'Mostrar';
    toggle.setAttribute('aria-pressed', String(reveal));
    toggle.setAttribute('aria-label', reveal ? 'Ocultar contraseña' : 'Mostrar contraseña');
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const submit = node<HTMLButtonElement>('#access-submit');
    feedback.hidden = true;
    submit.disabled = true;
    submit.textContent = 'Comprobando acceso…';
    form.setAttribute('aria-busy', 'true');
    try {
      await signIn({ email: node<HTMLInputElement>('#access-email').value.trim(), password: password.value });
    } catch (error) {
      feedback.textContent = error instanceof AuthNotConfiguredError ? error.message : 'No pudimos comprobar el acceso. Inténtalo más tarde.';
      feedback.hidden = false;
      feedback.focus();
    } finally {
      password.value = '';
      password.type = 'password';
      toggle.textContent = 'Mostrar';
      toggle.setAttribute('aria-pressed', 'false');
      toggle.setAttribute('aria-label', 'Mostrar contraseña');
      submit.disabled = false;
      submit.textContent = 'Iniciar sesión';
      form.setAttribute('aria-busy', 'false');
    }
  });
  const registration = node<HTMLFormElement>('#register-form');
  const registerPassword = node<HTMLInputElement>('#register-password');
  const registerConfirm = node<HTMLInputElement>('#register-confirm');
  const registerFeedback = node('#register-feedback');
  const registerToggle = node<HTMLButtonElement>('#register-password-toggle');
  function clearRegistrationPasswords() {
    registerPassword.value = ''; registerConfirm.value = ''; registerPassword.type = 'password';
    registerToggle.textContent = 'Mostrar'; registerToggle.setAttribute('aria-pressed', 'false'); registerToggle.setAttribute('aria-label', 'Mostrar contraseña');
  }
  registerToggle.addEventListener('click', () => {
    const show = registerPassword.type === 'password'; registerPassword.type = show ? 'text' : 'password';
    registerToggle.textContent = show ? 'Ocultar' : 'Mostrar'; registerToggle.setAttribute('aria-pressed', String(show)); registerToggle.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
  });
  registration.addEventListener('submit', async event => {
    event.preventDefault(); registerFeedback.hidden = true;
    if (!registration.reportValidity()) return;
    if (registerPassword.value !== registerConfirm.value) {
      registerFeedback.textContent = 'Las contraseñas no coinciden. Revisa ambos campos.'; registerFeedback.hidden = false; registerConfirm.focus(); return;
    }
    const button = node<HTMLButtonElement>('#register-submit'); button.disabled = true; button.textContent = 'Creando cuenta…'; registration.setAttribute('aria-busy', 'true');
    try { await signUp({name: node<HTMLInputElement>('#register-name').value.trim(), email: node<HTMLInputElement>('#register-email').value.trim(), password: registerPassword.value}); }
    catch (error) { registerFeedback.textContent = error instanceof AuthNotConfiguredError ? 'El registro aún no está disponible. Tu carrito se conserva; podrás continuar cuando habilitemos las cuentas.' : 'No pudimos crear tu cuenta. Inténtalo más tarde.'; registerFeedback.hidden = false; registerFeedback.focus(); }
    finally { clearRegistrationPasswords(); button.disabled = false; button.textContent = 'Crear cuenta'; registration.setAttribute('aria-busy', 'false'); }
  });
  node('#account').addEventListener('click', () => { location.hash = 'acceso'; });

  function route(): void {
    const isRegister = location.hash === '#registro';
    const isAccess = location.hash === '#acceso' || isRegister;
    clearRegistrationPasswords(); registerFeedback.hidden = true;
    if (isRegister) { password.value = ''; feedback.hidden = true; }
    const isAdmin = location.hash === '#admin' || location.hash.startsWith('#admin/');
    if (!isAccess) {
      password.value = '';
      password.type = 'password';
      toggle.textContent = 'Mostrar';
      toggle.setAttribute('aria-pressed', 'false');
      toggle.setAttribute('aria-label', 'Mostrar contraseña');
    }
    document.body.classList.toggle('admin-mode', isAdmin);
    if (!isAccess && !isAdmin) { password.value = ''; feedback.hidden = true; return; }
    for (const child of node('main').children) if (child instanceof HTMLElement) child.hidden = child.id !== (isAdmin ? 'admin-page' : 'access-page');
    if (isAccess) {
      document.title = `${isRegister ? 'Crear cuenta' : 'Acceso'} — Bagstore`;
      form.hidden = isRegister; registration.hidden = !isRegister;
      node('#access-title').textContent = isRegister ? 'Tu próxima favorita te espera.' : 'Bienvenida de nuevo.';
      node('.access-intro').textContent = isRegister ? 'Crea tu cuenta para comprar y consultar tus pedidos.' : 'Ingresa a tu espacio de Bagstore.';
      node('#purchase-access-note').hidden = !purchaseDestination();
      for (const [id, active] of [['login-tab', !isRegister], ['register-tab', isRegister]] as const) {
        if (active) node('#' + id).setAttribute('aria-current', 'page'); else node('#' + id).removeAttribute('aria-current');
      }
      node('#access-title').focus({ preventScroll: true });
    } else {
      const requested = location.hash.split('/')[1] ?? 'resumen';
      const section: AdminSection = Object.hasOwn(sections, requested) ? requested as AdminSection : 'resumen';
      const details = sections[section];
      node('#admin-title').textContent = details.title;
      node('#admin-subtitle').textContent = details.subtitle;
      document.title = `Administración · ${section} — Bagstore`;
      document.querySelectorAll<HTMLElement>('[data-admin-section]').forEach(view => { view.hidden = view.dataset.adminSection !== section; });
      document.querySelectorAll<HTMLAnchorElement>('[data-admin-link]').forEach(link => {
        const active = link.dataset.adminLink === section;
        link.classList.toggle('active', active);
        if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
      });
      node('#admin-title').focus({ preventScroll: true });
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  setupProductManager(catalogs);
  window.addEventListener('hashchange', route);
  route();
}
