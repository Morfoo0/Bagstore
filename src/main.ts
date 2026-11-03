import './styles.css';
import { products } from './data/products';
import { bagArt } from './components/bag';
import type { Category } from './types/product';

function el<T extends HTMLElement>(selector: string): T {
  const result = document.querySelector<T>(selector);
  if (!result) throw new Error(`Elemento requerido no encontrado: ${selector}`);
  return result;
}
const money = (value: number): string => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(value);
let category: Category = 'Todas';
let searchTerm = '';
const cart = new Map<number, number>();
let toastTimer: ReturnType<typeof setTimeout>;

el('#hero-bag').innerHTML = bagArt(products[0], 'hero');
el('#year').textContent = String(new Date().getFullYear());

function notify(message: string): void {
  clearTimeout(toastTimer);
  const toast = el('#toast');
  toast.textContent = message;
  toast.classList.add('visible');
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 2600);
}
function renderProducts(): void {
  const visible = products.filter(p => (category === 'Todas' || p.category === category) && `${p.name} ${p.label} ${p.category}`.toLocaleLowerCase('es').includes(searchTerm));
  el('#products').innerHTML = visible.map(p => `<article class="product-card"><div class="product-image"><span class="product-tag">${p.category.toUpperCase()}</span>${bagArt(p, 'catalog')}</div><div class="product-meta"><div class="product-title"><h3>${p.name}</h3><span>${money(p.price)}</span></div><p class="product-color"><span class="swatch" style="background:${p.color}" aria-hidden="true"></span>${p.label} · MXN</p></div><button class="add-button" data-add="${p.id}" aria-label="Agregar ${p.name} a la bolsa">Agregar a mi bolsa <span aria-hidden="true">+</span></button></article>`).join('');
  el('#empty').hidden = visible.length > 0;
  el('#results').textContent = `${visible.length} ${visible.length === 1 ? 'bolsa' : 'bolsas'}`;
  document.querySelectorAll<HTMLButtonElement>('[data-filter]').forEach(button => {
    const selected = button.dataset.filter === category;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
}
function setCategory(value: string): void {
  if (!['Todas', 'Tote', 'Crossbody', 'Mini'].includes(value)) return;
  category = value as Category;
  renderProducts();
}
function renderCart(): void {
  const count = [...cart.values()].reduce((sum, value) => sum + value, 0);
  el('#cart-count').textContent = String(count);
  el('#drawer-count').textContent = `(${count})`;
  el('#cart-open').setAttribute('aria-label', `Abrir bolsa de compras, ${count} productos`);
  let total = 0;
  el('#cart-items').innerHTML = [...cart].map(([id, quantity]) => {
    const p = products.find(product => product.id === id)!;
    total += p.price * quantity;
    return `<article class="cart-item"><div class="cart-art">${bagArt(p, 'cart')}</div><div><h3>${p.name}</h3><p>${p.label} · ${money(p.price)} MXN</p><div class="quantity"><button data-quantity="${id}" data-delta="-1" aria-label="Quitar una unidad de ${p.name}">−</button><span aria-label="Cantidad">${quantity}</span><button data-quantity="${id}" data-delta="1" ${quantity >= 10 ? 'disabled' : ''} aria-label="Agregar una unidad de ${p.name}">+</button><button class="remove" data-remove="${id}" aria-label="Eliminar ${p.name}">Eliminar</button></div></div></article>`;
  }).join('') || '<div class="cart-empty">Tu bolsa está esperando su primera favorita.<br/>Explora la colección y agrega una bolsa.</div>';
  el('#cart-summary').innerHTML = count ? `<p class="cart-total"><span>Subtotal de ejemplo</span><strong>${money(total)} MXN</strong></p><p class="demo-note">Cantidades limitadas a 10 por producto para esta prueba. No representa stock real. Envíos, pagos y precios definitivos pendientes de integración con el backend.</p>` : '';
}
function info(title: string, text: string): void {
  el('#info-title').textContent = title;
  el('#info-text').textContent = text;
  el<HTMLDialogElement>('#info-dialog').showModal();
}
el('#menu-toggle').addEventListener('click', () => {
  const open = el('#navigation').classList.toggle('open');
  el('#menu-toggle').setAttribute('aria-expanded', String(open));
  el('#menu-toggle').setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
});
function closeMenu(): void {
  el('#navigation').classList.remove('open');
  el('#menu-toggle').setAttribute('aria-expanded', 'false');
  el('#menu-toggle').setAttribute('aria-label', 'Abrir menú');
}
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && el('#navigation').classList.contains('open')) { closeMenu(); el('#menu-toggle').focus(); }
});
el('#navigation').addEventListener('click', event => {
  const link = (event.target as HTMLElement).closest<HTMLAnchorElement>('a');
  if (!link) return;
  if (link.dataset.category) { searchTerm = ''; el<HTMLInputElement>('#search-input').value = ''; setCategory(link.dataset.category); }
  closeMenu();
});
document.querySelectorAll<HTMLButtonElement>('[data-filter]').forEach(button => button.addEventListener('click', () => setCategory(button.dataset.filter!)));
el('#search').addEventListener('submit', event => {
  event.preventDefault();
  searchTerm = el<HTMLInputElement>('#search-input').value.trim().toLocaleLowerCase('es');
  category = 'Todas';
  renderProducts();
  el('#catalogo').scrollIntoView();
});
el('#clear-search').addEventListener('click', () => { searchTerm = ''; el<HTMLInputElement>('#search-input').value = ''; setCategory('Todas'); });
el('#products').addEventListener('click', event => {
  const button = (event.target as HTMLElement).closest<HTMLButtonElement>('[data-add]');
  if (!button) return;
  const id = Number(button.dataset.add);
  const quantity = cart.get(id) ?? 0;
  if (quantity >= 10) return notify('Límite de demostración: 10 unidades por producto.');
  cart.set(id, quantity + 1);
  renderCart();
  notify('Agregaste una favorita a tu bolsa.');
});
el('#cart-items').addEventListener('click', event => {
  const button = (event.target as HTMLElement).closest<HTMLButtonElement>('button');
  if (!button) return;
  if (button.dataset.remove) cart.delete(Number(button.dataset.remove));
  if (button.dataset.quantity) {
    const id = Number(button.dataset.quantity);
    const quantity = (cart.get(id) ?? 0) + Number(button.dataset.delta);
    if (quantity <= 0) cart.delete(id); else cart.set(id, Math.min(quantity, 10));
  }
  renderCart();
  // Conservar foco de teclado al reconstruir la lista después de cambiar cantidades.
  const id = button.dataset.quantity;
  const replacement = id ? document.querySelector<HTMLButtonElement>(`[data-quantity="${id}"][data-delta="${button.dataset.delta}"]:not(:disabled)`) : null;
  (replacement ?? document.querySelector<HTMLButtonElement>('#cart-items button') ?? el<HTMLButtonElement>('[data-close="cart-dialog"]')).focus();
});
el('#cart-open').addEventListener('click', () => el<HTMLDialogElement>('#cart-dialog').showModal());
document.querySelectorAll<HTMLButtonElement>('[data-close]').forEach(button => button.addEventListener('click', () => el<HTMLDialogElement>(`#${button.dataset.close}`).close()));
el('#account').addEventListener('click', () => info('Tu cuenta, próximamente', 'La pantalla de acceso es parte del siguiente entregable. El inicio de sesión real dependerá de la API del equipo de backend. Por ahora no solicitamos ni guardamos contraseñas.'));
el('#returns-info').addEventListener('click', () => info('Cambios y devoluciones', 'El formulario y la política se definirán con el equipo. Esta demostración todavía no procesa solicitudes de devolución.'));
renderProducts();
renderCart();
