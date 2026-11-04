import type { Product } from '../types/product';
export interface DemoCollection { id: string; name: string; description: string; productIds: number[]; active: boolean; }
export interface Review { id: string; productId: number; name: string; rating: number; comment: string; date: string; }
export interface OrderItem { productId: number; name: string; qty: number; price: number; }
export interface DemoOrder { id: string; date: string; items: OrderItem[]; subtotal: number; discount: number; shipping: number; total: number; delivery: string; payment: string; }
export interface DemoReturn { id: string; orderId: string; productId: number; reason: string; comment: string; status: 'Solicitada' | 'En revisión' | 'Resuelta'; date: string; }
interface StockChange { id: string; productId: number; quantity: number; reason: string; date: string; }
interface State { collections: DemoCollection[]; reviews: Review[]; orders: DemoOrder[]; returns: DemoReturn[]; stock: Record<string, number>; changes: StockChange[]; }
interface StoragePort { getItem(key: string): string | null; setItem(key: string, value: string): void; }
export const COMMERCE_KEY = 'bagstore.commerce.v1';
const round = (n: number) => Math.round(n * 100) / 100;
const idOK = (id: unknown): id is string => typeof id === 'string' && /^[a-z0-9-]+$/i.test(id);
const textOK = (value: unknown, min: number, max: number): value is string => typeof value === 'string' && value.trim().length >= min && value.length <= max;
const dateOK = (value: unknown) => typeof value === 'string' && Number.isFinite(Date.parse(value));
const integer = (n: unknown, min = 0, max = 99999): n is number => Number.isInteger(n) && Number(n) >= min && Number(n) <= max;
function validState(s: State) {
  return s && Array.isArray(s.collections) && s.collections.every(c => idOK(c.id) && textOK(c.name, 2, 60) && textOK(c.description, 0, 500) && typeof c.active === 'boolean' && Array.isArray(c.productIds) && c.productIds.every(id => integer(id, 1)))
    && Array.isArray(s.reviews) && s.reviews.every(r => idOK(r.id) && integer(r.productId, 1) && textOK(r.name, 2, 40) && integer(r.rating, 1, 5) && textOK(r.comment, 5, 1000) && dateOK(r.date))
    && Array.isArray(s.orders) && s.orders.every(o => idOK(o.id) && dateOK(o.date) && Array.isArray(o.items) && o.items.every(i => integer(i.productId, 1) && textOK(i.name, 1, 80) && integer(i.qty, 1, 10) && Number.isFinite(i.price) && i.price > 0) && [o.total, o.subtotal, o.discount, o.shipping].every(n => Number.isFinite(n) && n >= 0) && textOK(o.delivery, 1, 50) && textOK(o.payment, 1, 50))
    && Array.isArray(s.returns) && s.returns.every(r => idOK(r.id) && idOK(r.orderId) && integer(r.productId, 1) && textOK(r.reason, 2, 80) && textOK(r.comment, 5, 1000) && ['Solicitada', 'En revisión', 'Resuelta'].includes(r.status) && dateOK(r.date))
    && s.stock && typeof s.stock === 'object' && Object.entries(s.stock).every(([key, n]) => /^\d+$/.test(key) && integer(n))
    && Array.isArray(s.changes) && s.changes.every(c => idOK(c.id) && integer(c.productId, 1) && integer(c.quantity) && textOK(c.reason, 3, 200) && dateOK(c.date));
}
export function createCommerceRepository(storage?: StoragePort) {
  let state: State = { collections: [{ id: 'everyday', name: 'Everyday essentials', description: 'Tus esenciales para acompañarte todos los días.', productIds: [1, 2, 3, 4], active: true }], reviews: [], orders: [], returns: [], stock: {}, changes: [] };
  let warning = '';
  let seq = 0;
  const id = (prefix: string) => `${prefix}-${Date.now()}-${++seq}`;
  try { const raw = storage?.getItem(COMMERCE_KEY); if (raw) { const saved = JSON.parse(raw); if (!validState(saved)) throw Error(); state = saved; } }
  catch { warning = 'No pudimos recuperar colecciones, inventario o pedidos locales. Se usan datos iniciales de demostración.'; }
  function persist() { try { if (!storage) throw Error(); storage.setItem(COMMERCE_KEY, JSON.stringify(state)); warning = ''; } catch { warning = 'El navegador no pudo guardar estos cambios. Solo permanecerán en memoria durante esta página.'; } }
  const quantity = (productId: number) => state.stock[String(productId)] ?? 20;
  return {
    warning: () => warning,
    collections: () => structuredClone(state.collections), reviews: (productId: number) => structuredClone(state.reviews.filter(r => r.productId === productId)),
    orders: () => structuredClone(state.orders), returns: () => structuredClone(state.returns), changes: () => structuredClone(state.changes), quantity,
    saveCollection(name: string, description: string, productIds: number[], existingId?: string) {
      if (!textOK(name, 2, 60) || !textOK(description, 0, 500)) throw Error('La colección requiere nombre de 2–60 caracteres y descripción de hasta 500.');
      const key = name.trim().toLocaleLowerCase('es');
      if (state.collections.some(c => c.id !== existingId && c.name.toLocaleLowerCase('es') === key)) throw Error('Ya existe una colección con ese nombre.');
      if (!productIds.every(p => integer(p, 1))) throw Error('Selecciona productos válidos.');
      const previous = state.collections.find(c => c.id === existingId);
      if (existingId && !previous) throw Error('No encontramos esa colección.');
      const c: DemoCollection = { id: existingId ?? id('col'), name: name.trim(), description: description.trim(), productIds: [...new Set(productIds)], active: previous?.active ?? true };
      if (previous) state.collections[state.collections.indexOf(previous)] = c; else state.collections.push(c);
      persist(); return structuredClone(c);
    },
    toggleCollection(collectionId: string) { const c = state.collections.find(c => c.id === collectionId); if (!c) throw Error('Colección no encontrada.'); c.active = !c.active; persist(); },
    setStock(productId: number, count: number, reason: string) { if (!integer(productId, 1) || !integer(count) || !textOK(reason, 3, 200)) throw Error('Usa una cantidad entera de 0–99,999 e indica un motivo de 3–200 caracteres.'); state.stock[String(productId)] = count; state.changes.unshift({ id: id('stock'), productId, quantity: count, reason: reason.trim(), date: new Date().toISOString() }); persist(); },
    addReview(productId: number, name: string, rating: number, comment: string) {
      if (!integer(productId, 1) || !textOK(name, 2, 40) || !integer(rating, 1, 5) || !textOK(comment, 5, 1000)) throw Error('Indica un nombre de 2–40 caracteres, entre 1 y 5 estrellas y un comentario de 5–1,000 caracteres.');
      state.reviews.unshift({ id: id('review'), productId, name: name.trim(), rating, comment: comment.trim(), date: new Date().toISOString() }); persist();
    },
    createOrder(lines: { id: number; qty: number }[], products: Product[], coupon: boolean, shipping: number, delivery: string, payment: string) {
      if (!lines.length || new Set(lines.map(l => l.id)).size !== lines.length || ![0, 79].includes(shipping) || !['Recoger en tienda (demo)', 'Envío a domicilio (demo)'].includes(delivery) || !['Tarjeta de prueba', 'Transferencia de prueba'].includes(payment)) throw Error('Revisa los productos y las opciones de entrega y pago.');
      if ((delivery === 'Recoger en tienda (demo)' && shipping !== 0) || (delivery === 'Envío a domicilio (demo)' && shipping !== 79)) throw Error('La tarifa no corresponde a la entrega seleccionada. Revisa tus opciones.');
      const items = lines.map(line => { const p = products.find(p => p.id === line.id); if (!p || !Number.isFinite(p.price) || p.price <= 0 || !integer(line.qty, 1, 10) || line.qty > quantity(line.id)) throw Error('La cantidad seleccionada supera la disponibilidad de un producto. Revisa tu carrito.'); return { productId: p.id, name: p.name, price: p.price, qty: line.qty }; });
      const subtotal = round(items.reduce((n, p) => n + p.price * p.qty, 0)); const discount = coupon ? round(subtotal * .1) : 0;
      const order: DemoOrder = { id: id('demo'), date: new Date().toISOString(), items, subtotal, discount, shipping, total: round(subtotal - discount + shipping), delivery, payment };
      for (const p of items) state.stock[String(p.productId)] = quantity(p.productId) - p.qty;
      state.orders.unshift(order); persist(); return structuredClone(order);
    },
    requestReturn(orderId: string, productId: number, reason: string, comment: string) {
      const order = state.orders.find(o => o.id === orderId);
      if (!order?.items.some(p => p.productId === productId) || !textOK(reason, 2, 80) || !textOK(comment, 5, 1000)) throw Error('Selecciona un pedido y producto válidos e indica un motivo con descripción de 5–1,000 caracteres.');
      if (state.returns.some(r => r.orderId === orderId && r.productId === productId && r.status !== 'Resuelta')) throw Error('Ya existe una solicitud abierta para este producto y pedido.');
      const r: DemoReturn = { id: id('dev'), orderId, productId, reason, comment: comment.trim(), status: 'Solicitada', date: new Date().toISOString() }; state.returns.unshift(r); persist(); return { ...r };
    },
    setReturnStatus(returnId: string, status: DemoReturn['status']) { const r = state.returns.find(r => r.id === returnId); if (!r || !['Solicitada', 'En revisión', 'Resuelta'].includes(status)) throw Error('Solicitud o estado no válido.'); r.status = status; persist(); }
  };
}
export type CommerceRepository = ReturnType<typeof createCommerceRepository>;
export function csvCell(value: unknown): string { const s = String(value ?? ''); return `"${(/^[=+\-@\t\r]/.test(s) ? "'" : '') + s.replace(/"/g, '""')}"`; }
