import test from 'node:test';
import assert from 'node:assert/strict';
import { createCatalogRepository, normalizedName, legacyColorId, CATALOG_KEY } from '../src/services/catalogs.ts';
import { createProductRepository } from '../src/services/admin-products.ts';
function storage() { const map = new Map<string, string>(); return { getItem: (k: string) => map.get(k) ?? null, setItem: (k: string, v: string) => { map.set(k, v); } }; }

test('colores evitan duplicados por mayúsculas, espacios y acentos', () => {
  const repo = createCatalogRepository(storage());
  for (const name of ['ROJO', ' Rojo ', 'rojó', '  café  ', 'CAFE']) assert.throws(() => repo.addColor(name, '#AA0000'));
  assert.equal(repo.colors().length, 10);
  assert.equal(normalizedName('  Azul   MARÍNO  '), 'azul marino');
});
test('color nuevo conserva su ID y tono al recargar', () => {
  const memory = storage(); const repo = createCatalogRepository(memory);
  const color = repo.addColor('  Morado ', '#663399');
  assert.equal(color.name, 'Morado');
  assert.deepEqual(createCatalogRepository(memory).colors().find(c => c.id === color.id), color);
});
test('categorías se crean y renombran sin cambiar su identificador', () => {
  const repo = createCatalogRepository(storage());
  const category = repo.addCategory('Mochila');
  assert.equal(repo.renameCategory(category.id, 'Mochilas').id, category.id);
  assert.throws(() => repo.addCategory('  MOCHILAS '));
  assert.throws(() => repo.renameCategory(category.id, 'TOTE'));
});
test('producto admite categoría nueva e IDs estables de categoría y color', () => {
  const memory = storage(); const catalogs = createCatalogRepository(memory);
  const category = catalogs.addCategory('Mochila');
  const color = catalogs.addColor('Morado', '#663399');
  const repo = createProductRepository([], memory, () => catalogs.categories().map(c => c.name));
  const p = repo.save({ name: 'Mochila Aurora', category: category.name, categoryId: category.id, label: color.name, colorId: color.id, color: color.tone, accent: '#493A30', price: '499.90' });
  catalogs.renameCategory(category.id, 'Mochilas');
  const recovered = createProductRepository([], memory, () => catalogs.categories().map(c => c.name)).list()[0];
  assert.equal(recovered.categoryId, category.id);
  assert.equal(recovered.colorId, color.id);
  assert.equal(catalogs.categories().find(c => c.id === p.categoryId)?.name, 'Mochilas');
});
test('migración reconoce tonos anteriores sin generar colores duplicados', () => {
  assert.equal(legacyColorId('Caramelo'), 'color-cafe');
  assert.equal(legacyColorId('Cacao'), 'color-cafe');
  assert.equal(legacyColorId('Beige clásico'), 'color-beige');
  assert.equal(legacyColorId('Lino'), 'color-beige');
  assert.equal(legacyColorId('ROJO'), 'color-rojo');
});
test('producto anterior queda vinculado por ID antes de renombrar una categoría personalizada', () => {
  const memory = storage(); const catalogs = createCatalogRepository(memory);
  const category = catalogs.addCategory('Clutch');
  const repo = createProductRepository([{ id: 10, name: 'Clutch ejemplo', category: 'Clutch', label: 'Rojo', color: '#B83236', accent: '#493A30', price: 300 }], memory, () => catalogs.categories().map(c => c.name));
  repo.bindCatalogs(() => ({ categoryId: category.id, colorId: 'color-rojo' }));
  catalogs.renameCategory(category.id, 'Bolso de fiesta');
  const recovered = createProductRepository([], memory).list()[0];
  assert.equal(catalogs.categories().find(c => c.id === recovered.categoryId)?.name, 'Bolso de fiesta');
  assert.equal(recovered.colorId, 'color-rojo');
});
test('catálogo inválido usa básicos con aviso sin borrar almacenamiento', () => {
  const memory = storage(); memory.setItem(CATALOG_KEY, '{');
  const repo = createCatalogRepository(memory);
  assert.equal(repo.categories().length, 3);
  assert.ok(repo.warning());
  assert.equal(memory.getItem(CATALOG_KEY), '{');
});
test('nombres vacíos, tono inválido y fallo de almacenamiento se informan', () => {
  const repo = createCatalogRepository({ getItem: () => null, setItem: () => { throw Error(); } });
  assert.throws(() => repo.addCategory(' '));
  assert.throws(() => repo.addColor('Morado', 'purple'));
  repo.addColor('Morado', '#663399');
  assert.ok(repo.warning());
  assert.ok(repo.colors().some(c => c.name === 'Morado'));
});
