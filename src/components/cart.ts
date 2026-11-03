import { products } from '../data/products';
import { bagArt } from './bag';

const STORAGE_KEY = 'bagstore.cart.v1';
const DEMO_THRESHOLD = 1000;
const money = (value: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2 }).format(value);
function element<T extends HTMLElement = HTMLElement>(selector: string): T {
  const node = document.querySelector<T>(selector);
  if (!node) throw new Error(`Elemento de carrito no encontrado: ${selector}`);
  return node;
}

export function createCart(notify: (message: string) => void): { add: (id: number) => void } {
  const items = new Map<number, number>();
  let gift = false;
  let coupon = false;
  let couponMessage = '';
  let storageAvailable = true;
  try {
    const saved: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]');
    if (Array.isArray(saved)) for (const entry of saved) {
      if (Array.isArray(entry) && entry.length === 2 && products.some(p => p.id === entry[0]) && Number.isInteger(entry[1]) && entry[1] > 0 && entry[1] <= 10) items.set(entry[0], entry[1]);
    }
  } catch { storageAvailable = false; }

  function totals() {
    const subtotal = [...items].reduce((sum, [id, qty]) => sum + products.find(p => p.id === id)!.price * qty, 0);
    const discount = coupon ? Math.round(subtotal * 10) / 100 : 0;
    return { subtotal, discount, total: subtotal - discount, count: [...items.values()].reduce((sum, qty) => sum + qty, 0) };
  }
  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify([...items])); }
    catch { storageAvailable = false; }
  }
  function render() {
    const { subtotal, discount, total, count } = totals();
    element('#cart-count').textContent = String(count);
    element('#page-cart-count').textContent = `(${count} ${count === 1 ? 'producto' : 'productos'})`;
    element('#cart-open').setAttribute('aria-label', `Abrir carrito, ${count} ${count === 1 ? 'producto' : 'productos'}`);
    element('#cart-filled').hidden = count === 0;
    element('#cart-empty-state').hidden = count > 0;
    if (!count && location.hash === '#checkout') { location.hash = 'carrito'; return; }
    element('#cart-rows').innerHTML = [...items].map(([id, qty]) => {
      const product = products.find(p => p.id === id)!;
      return `<tr><td><div class="cart-product"><div class="cart-product-art">${bagArt(product, 'page-cart')}</div><div><h2>${product.name}</h2><p>Color: ${product.label}</p><span class="cart-reference">REF. BS-${String(id).padStart(3, '0')}</span><button class="cart-remove" data-remove="${id}" aria-label="Eliminar ${product.name}">Eliminar</button></div></div></td><td data-label="Precio">${money(product.price)}</td><td data-label="Cantidad"><div class="cart-stepper"><button data-id="${id}" data-delta="-1" aria-label="Quitar una unidad de ${product.name}">−</button><span aria-label="${qty} unidades">${qty}</span><button data-id="${id}" data-delta="1" ${qty >= 10 ? 'disabled' : ''} aria-label="Agregar una unidad de ${product.name}">+</button></div></td><td data-label="Subtotal" class="line-total">${money(product.price * qty)}</td></tr>`;
    }).join('');
    element('#summary-subtotal').textContent = money(subtotal);
    element('#summary-discount').textContent = `− ${money(discount)}`;
    element('#discount-row').hidden = !coupon;
    element('#summary-total').textContent = money(total);
    element('#coupon-feedback').textContent = couponMessage;
    element('#coupon-remove').hidden = !coupon;
    element<HTMLInputElement>('#coupon-code').disabled = coupon;
    element<HTMLButtonElement>('#coupon-apply').disabled = coupon;
    element<HTMLProgressElement>('#shipping-progress').value = Math.min(total, DEMO_THRESHOLD);
    element('#shipping-message').textContent = total >= DEMO_THRESHOLD ? '¡Alcanzaste la meta de envío de ejemplo!' : `Te faltan ${money(DEMO_THRESHOLD - total)} para la meta de envío de ejemplo.`;
    element('#cart-storage-note').textContent = storageAvailable ? 'Tu selección se guarda en este navegador. Máximo de prueba: 10 unidades por modelo.' : 'No se pudo guardar en este navegador. Tu selección se conservará solo mientras esta página esté abierta.';
    element('#review-items').innerHTML = [...items].map(([id, qty]) => {
      const product = products.find(p => p.id === id)!;
      return `<li><span>${product.name} <small>× ${qty}</small></span><strong>${money(product.price * qty)}</strong></li>`;
    }).join('');
    element('#review-total').textContent = money(total);
    element('#review-gift').textContent = gift ? 'Sí, marcado para regalo (ejemplo)' : 'Sin empaque de regalo';
    element('#review-discount').textContent = coupon ? `BEIGE10: −${money(discount)}` : 'Sin cupón';
  }
  function route() {
    const isCart = location.hash === '#carrito' || location.hash === '#checkout';
    const isCheckout = location.hash === '#checkout' && totals().count > 0;
    for (const child of element('main').children) if (child instanceof HTMLElement) child.hidden = child.id === 'cart-page' ? !isCart : isCart;
    element('#cart-view').hidden = isCheckout;
    element('#checkout-view').hidden = !isCheckout;
    element('#cart-step-1').classList.toggle('current', !isCheckout);
    element('#cart-step-2').classList.toggle('current', isCheckout);
    element('#cart-step-1').removeAttribute('aria-current');
    element('#cart-step-2').removeAttribute('aria-current');
    element(isCheckout ? '#cart-step-2' : '#cart-step-1').setAttribute('aria-current', 'step');
    document.title = isCart ? `${isCheckout ? 'Revisar compra' : 'Mi carrito'} — Bagstore` : 'Bagstore — Tu día, tu estilo.';
    if (isCart) {
      window.scrollTo({ top: 0, behavior: 'instant' });
      element(isCheckout ? '#checkout-title' : '#page-cart-title').focus({ preventScroll: true });
    }
  }
  element('#cart-open').addEventListener('click', () => {
    if (location.hash === '#carrito') route(); else location.hash = 'carrito';
  });
  element('#cart-rows').addEventListener('click', event => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>('button');
    if (!button) return;
    const id = Number(button.dataset.remove ?? button.dataset.id);
    if (!items.has(id)) return;
    if (button.dataset.remove) items.delete(id);
    else {
      const qty = (items.get(id) ?? 0) + Number(button.dataset.delta);
      if (qty <= 0) items.delete(id); else items.set(id, Math.min(qty, 10));
    }
    save(); render();
    const replacement = button.dataset.id ? document.querySelector<HTMLButtonElement>(`#cart-rows [data-id="${id}"][data-delta="${button.dataset.delta}"]:not(:disabled)`) : null;
    (replacement ?? document.querySelector<HTMLButtonElement>('#cart-rows button') ?? element('#cart-empty-link')).focus();
    notify('Carrito actualizado.');
  });
  element('#coupon-form').addEventListener('submit', event => {
    event.preventDefault();
    const input = element<HTMLInputElement>('#coupon-code');
    if (!input.value.trim()) { couponMessage = 'Escribe un código para probarlo.'; }
    else if (input.value.trim().toUpperCase() === 'BEIGE10') { coupon = true; couponMessage = 'BEIGE10 aplicado: 10% de descuento de ejemplo.'; }
    else couponMessage = 'Código no válido en esta demostración. Prueba BEIGE10.';
    render();
  });
  element('#coupon-remove').addEventListener('click', () => {
    coupon = false; couponMessage = 'Cupón retirado.';
    element<HTMLInputElement>('#coupon-code').value = '';
    render(); element<HTMLInputElement>('#coupon-code').focus();
  });
  element('#gift-option').addEventListener('change', event => { gift = (event.target as HTMLInputElement).checked; render(); });
  element('#checkout-button').addEventListener('click', () => { if (totals().count) location.hash = 'checkout'; });
  element('#demo-purchase').addEventListener('click', () => {
    element('#demo-order-message').hidden = false;
    element('#demo-order-message').focus();
  });
  window.addEventListener('hashchange', () => { element('#demo-order-message').hidden = true; route(); });
  render(); route();
  return { add(id) {
    if (!products.some(p => p.id === id)) return;
    const qty = items.get(id) ?? 0;
    if (qty >= 10) return notify('Límite de demostración: 10 unidades por producto.');
    items.set(id, qty + 1); save(); render(); notify('Agregaste una favorita a tu carrito.');
  } };
}
