import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiClient, ApiError, backendResource } from '../src/services/api.ts';
test('API envía JSON y credenciales solo a ruta configurada', async () => {
  let calls = 0;
  const client = new ApiClient('https://example.test', async (url, options) => {
    calls++; assert.equal(url, 'https://example.test/products'); assert.equal(options?.credentials, 'include');
    assert.equal(new Headers(options?.headers).get('Content-Type'), 'application/json');
    return Response.json({ id: 1 });
  });
  assert.deepEqual(await backendResource(client, {products:'/products'}, 'products').create({name:'Bolsa'}), {id:1});
  await assert.rejects(client.request('//other.test')); assert.equal(calls, 1);
  assert.throws(() => backendResource(client, {}, 'products').list());
});
test('API distingue sesión, permisos y error de servidor', async () => {
  for (const status of [401, 403, 500]) {
    const client = new ApiClient('https://example.test', async () => Response.json({}, {status}));
    await assert.rejects(client.request('/test'), (e: unknown) => e instanceof ApiError && e.status === status);
  }
});
test('API trata JSON inválido, respuesta vacía y caída de red', async () => {
  await assert.rejects(new ApiClient('https://example.test', async () => new Response('html')).request('/test'), /JSON/);
  assert.equal(await new ApiClient('https://example.test', async () => new Response(null, {status:204})).request('/test'), undefined);
  await assert.rejects(new ApiClient('https://example.test', async () => { throw Error(); }).request('/test'), /conectar/);
});
test('API cancela espera al superar tiempo límite', async () => {
  const client = new ApiClient('https://example.test', async (_, options) => new Promise((_, reject) => {
    options?.signal?.addEventListener('abort', () => reject(Error('abort')));
  }));
  await assert.rejects(client.request('/test', {}, 5), /tardó/);
});
