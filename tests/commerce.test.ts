import test from 'node:test';
import assert from 'node:assert/strict';
import { createCommerceRepository, COMMERCE_KEY, csvCell } from '../src/services/commerce.ts';
const product = { id: 1, name: 'Bolsa', price: 100.15 } as any;
function storage() { const data = new Map<string, string>(); return { getItem: (k: string) => data.get(k) ?? null, setItem: (k: string, v: string) => { data.set(k, v); } }; }
test('colecciones conservan asociaciones únicas, estado e identidad', () => {
  const memory = storage(); const repo = createCommerceRepository(memory);
  const c = repo.saveCollection('Nueva', 'Prueba', [1, 1, 2]);
  assert.deepEqual(c.productIds, [1, 2]);
  assert.throws(() => repo.saveCollection('NUEVA', '', []));
  repo.toggleCollection(c.id); repo.saveCollection('Otra', '', [2], c.id);
  assert.equal(createCommerceRepository(memory).collections().find(x => x.id === c.id)?.active, false);
});
test('pedido calcula centavos y descuento, descuenta stock y persiste sin referencias mutables', () => {
  const memory = storage(); const repo = createCommerceRepository(memory);
  const order = repo.createOrder([{ id: 1, qty: 3 }], [product], true, 79, 'Envío a domicilio (demo)', 'Tarjeta de prueba');
  assert.equal(order.subtotal, 300.45); assert.equal(order.discount, 30.05); assert.equal(order.total, 349.4);
  order.items[0].qty = 10;
  assert.equal(repo.orders()[0].items[0].qty, 3); assert.equal(createCommerceRepository(memory).quantity(1), 17);
});
test('pedido rechazado no modifica stock ni pedidos', () => {
  const repo = createCommerceRepository(storage()); repo.setStock(1, 1, 'Ajuste');
  for (const lines of [[{id:1,qty:2}], [{id:1,qty:1},{id:2,qty:1}], [{id:1,qty:1},{id:1,qty:1}]]) {
    assert.throws(() => repo.createOrder(lines, [product], false, 0, 'Recoger en tienda (demo)', 'Tarjeta de prueba'));
  }
  assert.equal(repo.quantity(1), 1); assert.equal(repo.orders().length, 0);
  assert.throws(() => repo.setStock(1, -1, 'Ajuste')); assert.throws(() => repo.setStock(1, 1.5, 'Ajuste'));
  assert.throws(() => repo.createOrder([{id:1,qty:1}], [product], false, 79, 'Recoger en tienda (demo)', 'Tarjeta de prueba'));
});
test('devoluciones requieren producto comprado y evitan solicitudes abiertas duplicadas', () => {
  const repo = createCommerceRepository(storage());
  const o = repo.createOrder([{id:1,qty:1}], [product], false, 0, 'Recoger en tienda (demo)', 'Transferencia de prueba');
  assert.throws(() => repo.requestReturn(o.id, 2, 'Cambio', 'Prueba de cambio'));
  const r = repo.requestReturn(o.id, 1, 'Cambio', 'Prueba de cambio');
  assert.throws(() => repo.requestReturn(o.id, 1, 'Cambio', 'Prueba de cambio'));
  repo.setReturnStatus(r.id, 'En revisión'); assert.equal(repo.returns()[0].status, 'En revisión');
  repo.setReturnStatus(r.id, 'Resuelta'); assert.equal(repo.quantity(1), 19);
});
test('reseñas validan límites y almacenamiento da aviso al fallar', () => {
  const repo = createCommerceRepository(); assert.throws(() => repo.addReview(1, 'Yo', 6, 'Prueba'));
  repo.addReview(1, 'Ana', 5, '<script>texto</script>');
  assert.equal(repo.reviews(1)[0].comment, '<script>texto</script>'); assert.ok(repo.warning());
  const memory = storage(); memory.setItem(COMMERCE_KEY, '{mal');
  assert.ok(createCommerceRepository(memory).warning());
});
test('CSV escapa comillas y fórmulas', () => {
  assert.equal(csvCell('=SUM(1)'), '"\'=SUM(1)"'); assert.equal(csvCell('a"b'), '"a""b"');
});
