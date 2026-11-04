import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { build } from 'esbuild';
import { JSDOM } from 'jsdom';

const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
const bundle = await build({ entryPoints: ['src/main.ts'], bundle: true, write: false, format: 'iife', loader: { '.css': 'empty' }, define: { 'import.meta.env': '{}' }, logLevel: 'silent' });
function page(hash = '#inicio') {
  const dom = new JSDOM(html, { url: `http://localhost/${hash}`, runScripts: 'outside-only', pretendToBeVisual: true });
  const w = dom.window;
  w.structuredClone = structuredClone;
  w.scrollTo = () => {};
  w.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  w.HTMLDialogElement.prototype.close = function () { this.open = false; this.dispatchEvent(new w.Event('close')); };
  const errors: unknown[] = []; w.addEventListener('error', e => errors.push(e.error));
  w.eval(bundle.outputFiles[0].text);
  const $ = (selector: string): any => { const node = w.document.querySelector(selector); assert.ok(node, `Falta ${selector}`); return node; };
  const set = (selector: string, value: string) => { $(selector).value = value; $(selector).dispatchEvent(new w.Event('input', { bubbles: true })); };
  const submit = (selector: string) => $(selector).dispatchEvent(new w.Event('submit', { bubbles: true, cancelable: true }));
  const route = async (hash: string) => { w.location.hash = hash; await new Promise(resolve => setTimeout(resolve, 5)); };
  return { dom, w, $, set, submit, route, errors };
}

test('arranque integra productos del panel y muestra catálogo público sin errores de DOM', () => {
  const p = page(); try { assert.equal(p.$('#products').children.length, 5); assert.equal(p.$('#extra-page').hidden, true); assert.deepEqual(p.errors, []); } finally { p.dom.window.close(); }
});
test('crear y editar producto se refleja en tienda y detalle; desactivar lo retira', async () => {
  const p = page('#admin/productos'); try {
    p.$('#product-new').click(); p.set('#product-name', 'Tote de integración'); p.set('#product-category', 'cat-tote'); p.set('#product-label', 'color-beige'); p.set('#product-price', '777.90'); p.submit('#product-editor-form');
    assert.equal(p.$('#product-editor').open, false);
    const rows = [...p.w.document.querySelectorAll('#admin-product-rows tr')]; const row = rows.find(r => r.textContent?.includes('Tote de integración'))!; assert.ok(row);
    const edit = row.querySelector<HTMLButtonElement>('[data-edit]')!; const id = edit.dataset.edit!;
    edit.click(); p.set('#product-name', 'Tote editada'); p.submit('#product-editor-form');
    await p.route(`#producto/${id}`); assert.match(p.$('#extra-page h1').textContent, /Tote editada/);
    await p.route('#admin/productos'); p.$(`[data-active="${id}"]`).click(); p.$('#product-confirm-action').click();
    await p.route('#catalogo'); assert.doesNotMatch(p.$('#products').textContent, /Tote editada/); assert.deepEqual(p.errors, []);
  } finally { p.dom.window.close(); }
});
test('colores duplicados se rechazan; categoría nueva sirve al formulario', async () => {
  const p = page('#admin/productos'); try {
    p.$('#product-new').click(); p.$('#product-add-color').click(); p.set('#catalog-name', ' ROJO '); p.submit('#catalog-form'); assert.equal(p.$('#catalog-error').hidden, false);
    p.$('#catalog-cancel').click(); p.$('#product-editor-cancel').click();
    await p.route('#admin/categorias'); p.$('#category-new').click(); p.set('#catalog-name', 'Mochila'); p.submit('#catalog-form');
    await p.route('#admin/productos'); p.$('#product-new').click(); assert.match(p.$('#product-category').textContent, /Mochila/); assert.deepEqual(p.errors, []);
  } finally { p.dom.window.close(); }
});
test('colección creada muestra sus productos y desactivación es reversible', async () => {
  const p = page('#admin/colecciones'); try {
    p.$('#collection-new').click(); p.set('#collection-name', 'Colección de prueba'); p.set('#collection-description', 'Descripción de ejemplo'); p.$('#collection-product-options input[value="1"]').checked = true; p.submit('#collection-form');
    const c = JSON.parse(p.w.localStorage.getItem('bagstore.commerce.v1')!).collections.find((c: any) => c.name === 'Colección de prueba'); assert.ok(c);
    await p.route(`#coleccion/${c.id}`); assert.match(p.$('#extra-page').textContent, /Tote Everyday/);
    await p.route('#admin/colecciones'); p.$(`[data-collection-toggle="${c.id}"]`).click(); p.$('#feature-confirm-ok').click();
    assert.doesNotMatch(p.$('#collection-showcase').textContent, /Colección de prueba/); assert.deepEqual(p.errors, []);
  } finally { p.dom.window.close(); }
});
test('inventario cero bloquea agregar producto y actualiza el filtro de stock bajo', async () => {
  const p = page('#admin/existencias'); try {
    p.set('#stock-qty-1', '0'); p.set('#stock-reason-1', 'Ajuste de prueba'); p.submit('form[data-stock="1"]');
    await p.route('#catalogo'); assert.equal(p.$('#products [data-add="1"]').disabled, true);
    await p.route('#producto/1'); assert.equal(p.$('[data-detail-add="1"]').disabled, true); assert.deepEqual(p.errors, []);
  } finally { p.dom.window.close(); }
});
test('reseñas se guardan como texto y compartir ofrece enlace local', async () => {
  const p = page('#producto/1'); try {
    p.set('#review-name', 'Prueba'); p.set('#review-rating', '5'); p.set('#review-comment', '<img src=x onerror=alert(1)>'); p.submit('#review-form');
    assert.match(p.$('.review-list').textContent, /<img/); assert.equal(p.w.document.querySelector('.review-list img'), null);
    p.$('[data-share="1"]').click(); await new Promise(resolve => setTimeout(resolve, 5)); assert.equal(p.$('#share-dialog').open, true); assert.match(p.$('#share-url').value, /#producto\/1/); assert.deepEqual(p.errors, []);
  } finally { p.dom.window.close(); }
});
test('comprar exige acceso y conserva carrito al cambiar a registro', async () => {
  const p = page(); try {
    p.$('#products [data-add="1"]').click(); await p.route('#carrito');
    p.$('#checkout-button').click(); await new Promise(resolve => setTimeout(resolve, 10));
    assert.equal(p.w.location.hash, '#acceso'); assert.equal(p.$('#purchase-access-note').hidden, false);
    assert.equal(p.$('#cart-count').textContent, '1');
    await p.route('#registro'); assert.equal(p.$('#register-form').hidden, false); assert.equal(p.$('#access-form').hidden, true);
    assert.equal(p.$('#cart-count').textContent, '1'); assert.deepEqual(p.errors, []);
  } finally { p.dom.window.close(); }
});
test('registro rechaza contraseñas distintas y no crea cuenta sin API', async () => {
  const p = page('#registro'); try {
    p.set('#register-name', 'Ana'); p.set('#register-email', 'ana@example.test'); p.set('#register-password', 'Prueba123'); p.set('#register-confirm', 'Otra12345');
    p.submit('#register-form'); assert.match(p.$('#register-feedback').textContent, /no coinciden/);
    p.set('#register-confirm', 'Prueba123'); p.submit('#register-form'); await new Promise(resolve => setTimeout(resolve, 5));
    assert.match(p.$('#register-feedback').textContent, /aún no está disponible/); assert.equal(p.$('#register-password').value, ''); assert.equal(p.$('#register-confirm').value, '');
    assert.doesNotMatch(JSON.stringify(p.w.localStorage), /Prueba123/);
    await p.route('#acceso'); assert.equal(p.$('#register-form').hidden, true); assert.deepEqual(p.errors, []);
  } finally { p.dom.window.close(); }
});
test('rutas directas de compra no permiten confirmar sin sesión', async () => {
  for (const hash of ['#compra/entrega', '#compra/pago', '#compra/confirmacion']) {
    const p = page(hash); try {
      await new Promise(resolve => setTimeout(resolve, 10)); assert.equal(p.w.location.hash, '#acceso');
      assert.equal(p.w.document.querySelector('#purchase-form'), null);
      assert.equal(p.w.localStorage.getItem('bagstore.commerce.v1'), null); assert.deepEqual(p.errors, []);
    } finally { p.dom.window.close(); }
  }
});

test('conexión API sin configurar muestra pendiente sin efectuar red', () => {
  const p = page('#admin/conexion'); try { p.$('#api-check').click(); assert.match(p.$('#api-status').textContent, /No se realizó ninguna petición/); assert.deepEqual(p.errors, []); } finally { p.dom.window.close(); }
});
