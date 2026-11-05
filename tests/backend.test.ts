import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { readFile } from 'node:fs/promises';
import { JSDOM } from 'jsdom';

const serviceBundle = await build({entryPoints:['src/services/backend-catalog.ts'],bundle:true,write:false,format:'esm'});
const {BackendCatalog} = await import('data:text/javascript;base64,'+Buffer.from(serviceBundle.outputFiles[0].text).toString('base64'));
const {ApiClient} = await import('../src/services/api.ts');
const category = {id:7,nombre:'Tote Bags',slug:'tote-bags',estado:'activo',orden:0,total_productos:2,descripcion:null};
const image = {url:'https://images.example.test/tote.jpg',texto_alternativo:'Tote',orden:1,es_principal:true};
const detail = {id:42,nombre:'Tote del servidor',slug:'tote-del-servidor',precio:450.50,disponible:true,estado:'activo',categoria:{id:7,nombre:'Tote Bags',slug:'tote-bags'},sku:'TOTE-042',descripcion:'Descripción real del catálogo',existencias:3,imagenes:[image],colecciones:[]};
const summary = {id:42,nombre:detail.nombre,slug:detail.slug,precio:detail.precio,disponible:true,estado:'activo',categoria:detail.categoria,imagen_principal:image};
const collection = {id:9,nombre:'Verano',slug:'verano',descripcion:null,estado:'activo',imagen_portada_url:null,total_productos:1};
const page = (datos: any[], pagina = 1, total = datos.length) => ({datos,paginacion:{pagina,por_pagina:12,total,total_paginas:Math.ceil(total/12)}});

test('adaptador lee datos/paginacion, filtros y detalle con existencias reales', async () => {
  const urls: string[]=[];
  const api=new BackendCatalog(new ApiClient('https://example.test',async (url: any)=>{urls.push(String(url));return Response.json(String(url).includes('/42')?detail:page([summary]));}));
  const result=await api.products({categoria_id:7,pagina:2,nombre:'Bolsa azul',disponible:true});
  assert.equal(result.datos[0].id,42); assert.match(urls[0],/categoria_id=7/); assert.match(urls[0],/nombre=Bolsa\+azul/);
  const p=await api.product(42);assert.equal(p.existencias,3);assert.equal(p.imagen_principal.url,image.url);
});
test('PUT producto preserva imágenes y existencias; no manda SKU editable ni campos locales',async()=>{
  let body:any;let method='';
  const api=new BackendCatalog(new ApiClient('https://example.test',async (_:any,options:any)=>{body=JSON.parse(options.body);method=options.method;return Response.json(detail);}));
  await api.saveProduct({nombre:detail.nombre,descripcion:detail.descripcion,precio:detail.precio,categoria_id:7,existencias:3,estado:'activo',imagenes:[image],sku:'NO-CAMBIAR',colorId:'local',imageData:'data:image/jpeg;base64,abc'} as any,42);
  assert.equal(method,'PUT');assert.deepEqual(body.imagenes,[image]);assert.equal(body.existencias,3);
  assert.equal(body.sku,undefined);assert.equal(body.colorId,undefined);assert.equal(body.imageData,undefined);assert.equal(body.estado,'activo');
});
test('POST exige SKU, imágenes HTTP y cantidades válidas antes de enviar',async()=>{
  let calls=0; const api=new BackendCatalog(new ApiClient('https://example.test',async()=>{calls++;return Response.json(detail);}));
  const draft={nombre:detail.nombre,descripcion:null,precio:450.5,categoria_id:7,existencias:0,estado:'activo',imagenes:[],sku:'TOTE-42'};
  for(const invalid of [{sku:''},{existencias:-1},{precio:1.234},{imagenes:[{...image,url:'data:image/jpeg;base64,abc'}]},{imagenes:[image,{...image}]}]) await assert.rejects(api.saveProduct({...draft,...invalid}));
  assert.equal(calls,0);await api.saveProduct(draft);assert.equal(calls,1);
});
test('contratos inválidos se rechazan sin convertirlos en datos locales',async()=>{
  for(const data of [[summary],page([{...summary,precio:'450.50'}]),{datos:[],paginacion:{pagina:0}}]){
    const api=new BackendCatalog(new ApiClient('https://example.test',async()=>Response.json(data)));
    await assert.rejects(api.products(),/formato esperado/);
  }
});
test('API conserva errores estructurados por campo y DELETE maneja 204',async()=>{
  const api=new BackendCatalog(new ApiClient('https://example.test',async (_:any,o:any)=>o?.method==='DELETE'?new Response(null,{status:204}):Response.json({error:{codigo:'CONFLICTO_UNICIDAD',mensaje:'SKU repetido',detalles:[{campo:'sku',mensaje:'Ya está registrado'}]}},{status:409})));
  await assert.rejects(api.product(42),(e:any)=>e.status===409&&e.code==='CONFLICTO_UNICIDAD'&&e.details[0].campo==='sku');
  assert.equal(await api.remove('productos',42),undefined);
});
test('categorías y colecciones envían campos del contrato con PUT y membresía canónica',async()=>{
  const sent:any[]=[];const api=new BackendCatalog(new ApiClient('https://example.test',async(url:any,o:any)=>{sent.push({url,method:o.method,body:JSON.parse(o.body)});return Response.json(String(url).includes('categorias')?category:collection);}));
  await api.saveCategory({nombre:'Tote',descripcion:null,orden:2,estado:'activo'},7);
  await api.saveCollection({nombre:'Verano',descripcion:null,estado:'activo',imagen_portada_url:null,producto_ids:[42,42]},9);
  assert.equal(sent[0].method,'PUT');assert.equal(sent[0].body.orden,2);assert.deepEqual(sent[1].body.producto_ids,[42]);assert.equal(sent[1].method,'PUT');
});

const html=await readFile(new URL('../index.html',import.meta.url),'utf8');
const domBundle=await build({stdin:{contents:"import {setupBackendApp} from './src/components/backend-app'; window.startBackend=setupBackendApp;",resolveDir:process.cwd()},bundle:true,write:false,format:'iife',loader:{'.css':'empty'},logLevel:'silent'});
async function app(options:{fail?:boolean;admin?:boolean;storage?:Record<string,string>;handler?:(url:string,opts:any)=>Response|Promise<Response>}={}){
  const dom=new JSDOM(html,{url:'http://localhost/#catalogo',runScripts:'outside-only',pretendToBeVisual:true});const w=dom.window;
  w.structuredClone=structuredClone;w.scrollTo=()=>{};w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new w.Event('close'));};
  const calls:{url:string;opts:any}[]=[];const errors:unknown[]=[];w.addEventListener('error',e=>errors.push(e.error));
  for(const[k,v]of Object.entries(options.storage??{}))w.localStorage.setItem(k,v);
  w.fetch=async(url:any,opts:any)=>{calls.push({url:String(url),opts});if(options.fail)throw Error('offline');if(options.handler){const r=await options.handler(String(url),opts);if(r)return r;}
    const path=new URL(String(url)).pathname;return Response.json(path==='/api/categorias'?page([category]):path==='/api/colecciones'?page([collection]):path==='/api/colecciones/9'?collection:path==='/api/productos/42'?detail:path==='/api/productos'?page([summary]):{status:'ok'});};
  w.eval(domBundle.outputFiles[0].text);(w as any).startBackend('http://localhost',()=>options.admin===true);
  const wait=()=>new Promise(r=>setTimeout(r,20));await wait();
  const $=(s:string):any=>{const n=w.document.querySelector(s);assert.ok(n,s);return n;};
  const route=async(hash:string)=>{w.location.hash=hash;await wait();};
  return{dom,w,calls,errors,$,route,wait};
}
test('modo API usa catálogo remoto, deshabilita colores y agrega tras verificar detalle',async()=>{
  const p=await app();try{
    assert.match(p.$('#products').textContent,/Tote del servidor/);assert.doesNotMatch(p.$('#products').textContent,/Aurora|Everyday/);
    assert.equal(p.$('#public-color-filter').disabled,true);
    p.$('[data-api-add="42"]').click();await p.wait();assert.equal(p.$('#cart-count').textContent,'1');
    assert.deepEqual(JSON.parse(p.w.localStorage.getItem('bagstore.api-cart.v1')!),[[42,1]]);assert.equal(p.w.localStorage.getItem('bagstore.cart.v1'),null);
    await p.route('#producto/42');assert.match(p.$('#extra-page').textContent,/3 unidades/);assert.match(p.$('#extra-page').textContent,/TOTE-042/);assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
test('panel prepara SKU inmutable, imágenes y stock pero no escribe sin permiso verificado',async()=>{
  const p=await app();try{
    await p.route('#admin/productos');p.$('[data-api-edit="productos"]').click();await p.wait();
    assert.equal(p.$('#api-sku').readOnly,true);assert.equal(p.$('#api-existencias').value,'3');assert.equal(p.$('[data-img-url]').value,image.url);
    assert.equal(p.$('#api-write-form button[type="submit"]').disabled,true);
    p.$('#api-write-form').dispatchEvent(new p.w.Event('submit',{bubbles:true,cancelable:true}));await p.wait();
    assert.equal(p.calls.filter(c=>c.opts.method&&c.opts.method!=='GET').length,0);assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
test('formulario autorizado usa PUT y muestra errores de campo sin cerrar ni anunciar guardado',async()=>{
  const p=await app({admin:true,handler:(_u,o)=>o.method==='PUT'?Response.json({error:{codigo:'VALIDACION_FALLIDA',mensaje:'Revisa la categoría',detalles:[{campo:'categoria_id',mensaje:'Categoría inactiva'}]}},{status:422}):undefined as any});try{
    await p.route('#admin/productos');p.$('[data-api-edit="productos"]').click();await p.wait();
    p.$('#api-write-form').dispatchEvent(new p.w.Event('submit',{bubbles:true,cancelable:true}));await p.wait();
    const request=p.calls.find(c=>c.opts.method==='PUT')!;assert.ok(request);assert.deepEqual(JSON.parse(request.opts.body).imagenes,[image]);
    assert.match(p.$('[data-api-error="categoria_id"]').textContent,/Categoría inactiva/);assert.equal(p.$('#api-categoria_id').getAttribute('aria-invalid'),'true');
    assert.equal(p.$('.api-editor').open,true);assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
test('error de servidor no repone productos demo; carrito sin verificar no se borra',async()=>{
  const saved='[[42,2]]';const p=await app({fail:true,storage:{'bagstore.api-cart.v1':saved}});try{
    assert.doesNotMatch(p.$('#products').textContent,/Aurora|Everyday/);assert.match(p.$('#products').textContent,/verificar tu carrito/);
    assert.equal(p.w.localStorage.getItem('bagstore.api-cart.v1'),saved);assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
test('filtros, orden, colecciones y rutas de compra respetan modo API',async()=>{
  const p=await app();try{
    p.$('#public-category-filter').value='7';p.$('#public-category-filter').dispatchEvent(new p.w.Event('change'));await p.wait();assert.ok(p.calls.some(c=>c.url.includes('categoria_id=7')));
    p.$('#api-sort').value='precio_asc';p.$('#api-sort').dispatchEvent(new p.w.Event('change'));await p.wait();assert.ok(p.calls.some(c=>c.url.includes('orden=precio_asc')));
    await p.route('#coleccion/9');await p.wait();assert.ok(p.calls.some(c=>c.url.includes('coleccion_id=9')));
    await p.route('#compra/pago');await p.wait();assert.equal(p.w.location.hash,'#acceso');assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
test('nueva colección selecciona productos por nombre y edición incompleta queda bloqueada',async()=>{
  const p=await app({admin:true});try{
    await p.route('#admin/colecciones');p.$('[data-api-new="colecciones"]').click();await p.wait();
    assert.match(p.$('#api-write-form').textContent,/Tote del servidor/);assert.equal(p.$('input[name="producto_ids"]').value,'42');
    p.$('[data-editor-close]').click();p.$('[data-api-edit="colecciones"]').click();await p.wait();
    assert.equal(p.$('#api-write-form button[type="submit"]').disabled,true);assert.match(p.$('#api-write-status').textContent,/membresía administrativa completa/);
    assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
test('reintentar tras caída restaura carrito API sin borrarlo ni crear datos de demostración',async()=>{
  let offline=true;const p=await app({storage:{'bagstore.api-cart.v1':'[[42,2]]'},handler:()=>{if(offline)throw Error('offline');return undefined as any;}});try{
    assert.equal(p.$('#cart-open').disabled,true);offline=false;p.$('#products [data-api-retry]').click();await p.wait();await p.wait();
    assert.equal(p.$('#cart-open').disabled,false);assert.equal(p.$('#cart-count').textContent,'2');assert.match(p.$('#products').textContent,/Tote del servidor/);assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
