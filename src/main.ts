import { createCommerceRepository } from './services/commerce';
import { setupFeatures } from './components/features';
import './features.css';
import './styles.css';
import './cart.css';
import './access.css';
import './products.css';
import { setupAccess } from './components/access';
import { createCart } from './components/cart';
import { products } from './data/products';
import { bagArt } from './components/bag';
import type { Category } from './types/product';
import { createCatalogRepository, baseCategories, legacyColorId, normalizedName } from './services/catalogs';

import { setupBackendApp } from './components/backend-app';

const runtime = (import.meta as ImportMeta & {env: Record<string,string|undefined>}).env;
if (runtime.VITE_DATA_SOURCE === 'api') {
  setupBackendApp(runtime.VITE_API_BASE_URL || window.location.origin, undefined, runtime.VITE_INTEGRATED_BACKEND === '1');
} else {
function el<T extends HTMLElement>(selector: string): T {
  const result = document.querySelector<T>(selector);
  if (!result) throw new Error(`Elemento requerido no encontrado: ${selector}`);
  return result;
}
const money = (value: number): string => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2 }).format(value);
let category: Category = 'Todas';
let searchTerm = '';
let toastTimer: ReturnType<typeof setTimeout>;
let catalogStorage: Storage | undefined;
try { catalogStorage = localStorage; } catch { /* Los catálogos funcionarán en memoria. */ }
const catalogs = createCatalogRepository(catalogStorage);
const commerce = createCommerceRepository(catalogStorage);
let colorFilter = '';
const publicCategoryId = (name: string) => baseCategories.find(c => normalizedName(c.name) === normalizedName(name))?.id;
function escapeText(text: string): string { return text.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!); }
function renderCatalogOptions() {
  const types = el<HTMLSelectElement>('#public-category-filter');
  const colors = el<HTMLSelectElement>('#public-color-filter');
  types.replaceChildren(new Option('Todas', 'Todas'), ...catalogs.categories().map(c => new Option(c.name, c.id)));
  types.value = category;
  colors.replaceChildren(new Option('Todos los colores', ''), ...catalogs.colors().map(c => new Option(c.name, c.id)));
  colors.value = colorFilter;
}

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
  const visible = products.filter(p => (category === 'Todas' || (p.categoryId ?? publicCategoryId(p.category)) === category) && (!colorFilter || (p.colorId ?? legacyColorId(p.label)) === colorFilter) && `${escapeText(p.name)} ${p.label} ${p.category}`.toLocaleLowerCase('es').includes(searchTerm));
  el('#products').innerHTML = visible.map(p => `<article class="product-card"><a class="product-image product-image-link" href="#producto/${p.id}" aria-label="Ver ${escapeText(p.name)}"><span class="product-tag">${escapeText(catalogs.categories().find(c => c.id === (p.categoryId ?? publicCategoryId(p.category)))?.name.toUpperCase() ?? p.category.toUpperCase())}</span>${p.imageData ? `<img class="public-product-photo" src="${p.imageData}" alt="${escapeText(p.name)}"/>` : bagArt(p, 'catalog')}</a><div class="product-meta"><div class="product-title"><h3><a href="#producto/${p.id}">${escapeText(p.name)}</a></h3><span>${money(p.price)}</span></div><p class="product-color"><span class="swatch" style="background:${p.color}" aria-hidden="true"></span>${escapeText(catalogs.colors().find(c => c.id === (p.colorId ?? legacyColorId(p.label)))?.name ?? p.label)} · MXN</p></div><button class="add-button" data-add="${p.id}" ${commerce.quantity(p.id) === 0 ? 'disabled' : ''} aria-label="Agregar ${escapeText(p.name)} a la bolsa">${commerce.quantity(p.id) === 0 ? 'Agotado' : 'Agregar a mi bolsa'} <span aria-hidden="true">+</span></button></article>`).join('');
  el('#empty').hidden = visible.length > 0;
  el('#results').textContent = `${visible.length} ${visible.length === 1 ? 'bolsa' : 'bolsas'}`;
  document.querySelectorAll<HTMLButtonElement>('[data-filter]').forEach(button => {
    const selected = button.dataset.filter === 'Todas' ? category === 'Todas' : publicCategoryId(button.dataset.filter!) === category;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
}
function setCategory(value: string): void {
  const option = catalogs.categories().find(c => c.id === value || c.name === value || c.id === publicCategoryId(value));
  if (value !== 'Todas' && !option) return;
  category = value === 'Todas' ? 'Todas' : option!.id;
  el<HTMLSelectElement>('#public-category-filter').value = category;
  renderProducts();
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
  el<HTMLSelectElement>('#public-category-filter').value = 'Todas';
  renderProducts();
  location.hash = 'catalogo';
  el('#catalogo').scrollIntoView();
});
el('#clear-search').addEventListener('click', () => { searchTerm = ''; colorFilter = ''; el<HTMLSelectElement>('#public-color-filter').value = ''; el<HTMLInputElement>('#search-input').value = ''; setCategory('Todas'); });
el('#public-category-filter').addEventListener('change', event => setCategory((event.target as HTMLSelectElement).value));
el('#public-color-filter').addEventListener('change', event => { colorFilter = (event.target as HTMLSelectElement).value; renderProducts(); });
window.addEventListener('bagstore-catalogs-changed', () => { renderCatalogOptions(); renderProducts(); });
window.addEventListener('bagstore-products-changed', () => { renderCatalogOptions(); renderProducts(); });
window.addEventListener('bagstore-commerce-changed', renderProducts);
el('#products').addEventListener('click', event => {
  const button = (event.target as HTMLElement).closest<HTMLButtonElement>('[data-add]');
  if (!button) return;
  const id = Number(button.dataset.add);
  shoppingCart.add(id);
});
document.querySelectorAll<HTMLButtonElement>('[data-close]').forEach(button => button.addEventListener('click', () => el<HTMLDialogElement>(`#${button.dataset.close}`).close()));
el('#returns-info').addEventListener('click', () => { location.hash = 'devoluciones'; });
renderCatalogOptions(); renderProducts();


setupAccess(catalogs);
const shoppingCart = createCart(notify, commerce);
setupFeatures(commerce, catalogs, shoppingCart, notify);
renderCatalogOptions();

}
