// Comprobación de lectura contra Python real, a través del proxy del frontend.
import { build } from 'esbuild';
import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';

const origin = process.env.BAGSTORE_CHECK_ORIGIN || 'http://127.0.0.1:5173';
const service = await build({entryPoints:['src/services/backend-catalog.ts'],bundle:true,write:false,format:'esm'});
const {BackendCatalog} = await import('data:text/javascript;base64,'+Buffer.from(service.outputFiles[0].text).toString('base64'));
const http = await build({entryPoints:['src/services/api.ts'],bundle:true,write:false,format:'esm'});
const {ApiClient} = await import('data:text/javascript;base64,'+Buffer.from(http.outputFiles[0].text).toString('base64'));
const api = new BackendCatalog(new ApiClient(origin));
const health = await api.health();
const products = await api.products({pagina:1,por_pagina:3});
const categories = await api.categories();
const collections = await api.collections();
const detail = products.datos[0] ? await api.product(products.datos[0].id) : undefined;
if(categories.datos[0]) {
  const filtered = await api.products({categoria_id:categories.datos[0].id,orden:'precio_asc'});
  assert.ok(filtered.datos.every(p=>p.categoria.id===categories.datos[0].id));
}
const next = await api.products({pagina:2,por_pagina:3});
assert.equal(next.paginacion.pagina,2);
const bundle = await build({stdin:{contents:"import {setupBackendApp} from './src/components/backend-app';window.startBackend=setupBackendApp;",resolveDir:process.cwd()},bundle:true,write:false,format:'iife',loader:{'.css':'empty'}});
const dom = new JSDOM(await readFile('index.html','utf8'),{url:origin+'/#catalogo',runScripts:'outside-only'});
try {
  const w = dom.window;
  // fetch de Node exige el AbortController del mismo runtime.
  w.structuredClone=structuredClone; w.AbortController=AbortController; w.fetch=fetch; w.scrollTo=()=>{};
  const errors=[]; w.addEventListener('error',e=>errors.push(e.error));
  w.eval(bundle.outputFiles[0].text); w.startBackend(origin);
  for(let i=0;i<100 && w.document.querySelector('#catalogo').hasAttribute('aria-busy');i++) await new Promise(r=>setTimeout(r,100));
  // El arranque empieza restaurando el carrito antes de cargar el catálogo.
  for(let i=0;i<100 && !w.document.querySelector('[data-api-add]') && !w.document.querySelector('#products [role="alert"]') && w.document.querySelector('#empty').hidden;i++) await new Promise(r=>setTimeout(r,100));
  assert.equal(errors.length,0);
  assert.equal(w.document.querySelector('#products [role="alert"]'),null);
  if(products.paginacion.total) assert.ok(w.document.querySelector('[data-api-add]'));
  console.log(JSON.stringify({health,productosActivos:products.paginacion.total,categorias:categories.paginacion.total,colecciones:collections.paginacion.total,detalleValidado:!!detail,pagina2:next.datos.length,productosDOM:w.document.querySelectorAll('#products article').length,erroresDOM:errors.length,escrituras:0},null,2));
} finally { dom.window.close(); }
