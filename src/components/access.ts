import { products } from '../data/products';
import { bagArt } from './bag';
import { AuthNotConfiguredError, signIn } from '../services/auth';

function node<T extends HTMLElement = HTMLElement>(selector: string): T {
  const result = document.querySelector<T>(selector);
  if (!result) throw new Error(`Elemento de acceso no encontrado: ${selector}`);
  return result;
}

const sections = {
  resumen: { title: 'Todo empieza con una buena base.', subtitle: 'Un vistazo al espacio de trabajo de Bagstore.' },
  productos: { title: 'Tus productos.', subtitle: 'Consulta el catálogo de ejemplo. Alta, edición y desactivación: siguiente entrega.' },
  categorias: { title: 'Un lugar para cada estilo.', subtitle: 'Categorías de ejemplo utilizadas en el catálogo público.' },
  colecciones: { title: 'Colecciones con personalidad.', subtitle: 'Aquí se organizarán las colecciones y sus productos.' },
  existencias: { title: 'Cada bolsa cuenta.', subtitle: 'Aquí se consultarán y ajustarán las existencias autorizadas por el servidor.' },
  reportes: { title: 'Conoce tus resultados.', subtitle: 'Aquí se presentarán los reportes de ventas.' }
};
type AdminSection = keyof typeof sections;

export function setupAccess(): void {
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
  node('#account').addEventListener('click', () => { location.hash = 'acceso'; });
  const categories = [...new Set(products.map(product => product.category))];
  node('#admin-product-count').textContent = String(products.length);
  node('#admin-category-count').textContent = String(categories.length);
  node('#admin-product-rows').innerHTML = products.map(product => `<tr><td><div class="admin-product-name"><span>${bagArt(product, 'admin')}</span><div><strong>${product.name}</strong><small>BS-${String(product.id).padStart(3, '0')}</small></div></div></td><td>${product.category}</td><td>${product.label}</td><td>${new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(product.price)}</td><td><span class="admin-tag">Ejemplo</span></td></tr>`).join('');
  node('#admin-categories').innerHTML = categories.map(category => `<article class="admin-category"><span aria-hidden="true">◇</span><h3>${category}</h3><p>${products.filter(p => p.category === category).length} productos de ejemplo</p></article>`).join('');

  function route(): void {
    const isAccess = location.hash === '#acceso';
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
      document.title = 'Acceso — Bagstore';
      node('#access-title').focus({ preventScroll: true });
    } else {
      const requested = location.hash.split('/')[1] ?? 'resumen';
      const section: AdminSection = Object.hasOwn(sections, requested) ? requested as AdminSection : 'resumen';
      const details = sections[section];
      node('#admin-title').textContent = details.title;
      node('#admin-subtitle').textContent = details.subtitle;
      document.title = `Panel de demostración · ${section} — Bagstore`;
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
  window.addEventListener('hashchange', route);
  route();
}
