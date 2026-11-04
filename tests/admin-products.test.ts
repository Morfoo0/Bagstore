import test from 'node:test';
import assert from 'node:assert/strict';
import { createProductRepository, validateProduct, validProductPhoto, ADMIN_STORAGE_KEY } from '../src/services/admin-products.ts';

const seed = [{ id: 1, name: 'Tote ejemplo', category: 'Tote' as const, label: 'Arena', color: '#CDB89E', accent: '#948067', price: 599 }];
const draft = { name: '  Tote Aurora  ', category: 'Tote', label: '  Lino  ', color: '#CDB89E', accent: '#948067', price: '649.90' };
function memoryStorage() {
  const values = new Map<string, string>();
  return { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => { values.set(key, value); } };
}

test('rechaza precios inválidos, categorías ajenas y colores no válidos', () => {
  for (const price of ['', '-2', '0', 'NaN', 'Infinity', '1e3', '19.999', '1000000']) assert.ok(validateProduct({ ...draft, price }).price, price);
  assert.ok(validateProduct({ ...draft, category: 'Ajena', color: 'red' }).category);
  assert.ok(validateProduct({ ...draft, color: 'red' }).color);
  assert.deepEqual(validateProduct(draft), {});
});

test('crea producto, normaliza textos y lo recupera desde almacenamiento', () => {
  const storage = memoryStorage();
  const repo = createProductRepository(seed, storage);
  const created = repo.save(draft);
  assert.equal(created.id, 2);
  assert.equal(created.name, 'Tote Aurora');
  assert.equal(created.label, 'Lino');
  assert.equal(created.price, 649.9);
  assert.equal(created.active, true);
  assert.deepEqual(createProductRepository(seed, storage).list(), repo.list());
});

test('editar conserva ID y estado; desactivar es reversible sin borrar', () => {
  const repo = createProductRepository(seed, memoryStorage());
  repo.setActive(1, false);
  const edited = repo.save(draft, 1);
  assert.equal(edited.active, false);
  assert.equal(edited.id, 1);
  assert.equal(repo.list().length, 1);
  repo.setActive(1, true);
  assert.equal(repo.list()[0].active, true);
});

test('un ID desconocido no genera productos ni cambios silenciosos', () => {
  const repo = createProductRepository(seed, memoryStorage());
  assert.throws(() => repo.save(draft, 100));
  assert.throws(() => repo.setActive(100, false));
  assert.equal(repo.list().length, 1);
});

test('almacenamiento corrupto o con IDs duplicados recupera semillas con aviso', () => {
  for (const stored of ['{', JSON.stringify([{ ...seed[0], active: true }, { ...seed[0], active: true }]), JSON.stringify([{ ...seed[0], active: true, color: 'url(malicioso)' }])]) {
    const storage = memoryStorage(); storage.setItem(ADMIN_STORAGE_KEY, stored);
    const repo = createProductRepository(seed, storage);
    assert.equal(repo.list().length, 1);
    assert.ok(repo.warning());
  }
});

test('fallo de guardado mantiene trabajo en memoria e informa la limitación', () => {
  const repo = createProductRepository(seed, { getItem: () => null, setItem: () => { throw new Error('Bloqueado'); } });
  repo.save(draft);
  assert.equal(repo.list().length, 2);
  assert.match(repo.warning(), /solo permanecerán/);
});

test('la lista y los resultados no permiten mutar el repositorio por referencia', () => {
  const repo = createProductRepository(seed, memoryStorage());
  repo.list()[0].name = 'Mutado';
  assert.equal(repo.list()[0].name, seed[0].name);
  const saved = repo.save(draft); saved.name = 'Otro';
  assert.equal(repo.list()[1].name, 'Tote Aurora');
});

const pixel = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aPmUAAAAASUVORK5CYII=';
test('la foto persiste, se recupera y se puede retirar al editar', () => {
  const storage = memoryStorage();
  const repo = createProductRepository(seed, storage);
  const created = repo.save({ ...draft, imageData: pixel, imageName: 'foto.png' });
  const recovered = createProductRepository(seed, storage);
  assert.equal(recovered.list()[1].imageData, pixel);
  assert.equal(recovered.list()[1].imageName, 'foto.png');
  recovered.save({ ...draft, name: 'Aurora sin foto' }, created.id);
  assert.equal(recovered.list()[1].imageData, undefined);
});
test('rechaza URLs externas, SVG y fotos demasiado grandes', () => {
  for (const imageData of ['https://example.com/foto.jpg', 'data:image/svg+xml;base64,PHN2Zz4=', 'data:text/html;base64,SG9sYQ==', 'data:image/jpeg;base64,' + 'A'.repeat(600001)]) {
    assert.equal(validProductPhoto(imageData), false);
    assert.ok(validateProduct({ ...draft, imageData }).imageData);
  }
  assert.equal(validProductPhoto(pixel), true);
});
