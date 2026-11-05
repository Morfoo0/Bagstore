// Prueba del frontend contra una API y base aisladas, iniciadas por pytest.
import {build} from 'esbuild';
import {readFile} from 'node:fs/promises';
import {JSDOM} from 'jsdom';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const base=process.env.BAGSTORE_TEST_URL;
if(!base||!process.env.BAGSTORE_TEST_ADMIN_PASSWORD)throw Error('Ejecutar desde backend/tests: requiere una base de pruebas aislada.');
const password='Cliente-E2E-12345';const email='e2e-'+crypto.randomUUID()+'@example.test';
const login=await fetch(base+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:process.env.BAGSTORE_TEST_ADMIN_EMAIL,password:process.env.BAGSTORE_TEST_ADMIN_PASSWORD})});assert.equal(login.status,200);
const auth=await login.json();const adminCookie=login.headers.getSetCookie()[0].split(';')[0];
const productResponse=await fetch(base+'/api/productos',{method:'POST',headers:{'Content-Type':'application/json',Cookie:adminCookie,'X-CSRF-Token':auth.csrf},body:JSON.stringify({nombre:'Bolsa de recorrido E2E',sku:'E2E-'+crypto.randomBytes(5).toString('hex').toUpperCase(),precio:200,categoria_id:1,color_id:3,existencias:5,imagenes:[],estado:'activo'})});assert.equal(productResponse.status,201);const product=await productResponse.json();
const html=await readFile('index.html','utf8');const bundle=await build({stdin:{contents:"import {setupBackendApp} from './src/components/backend-app'; window.startBackend=setupBackendApp;",resolveDir:process.cwd()},bundle:true,write:false,format:'iife',loader:{'.css':'empty'}});
const dom=new JSDOM(html,{url:'http://127.0.0.1:5173/#catalogo',runScripts:'outside-only',pretendToBeVisual:true});const w=dom.window;let cookie='';const errors=[];
w.structuredClone=structuredClone;w.AbortController=AbortController;w.scrollTo=()=>{};Object.defineProperty(w,'crypto',{value:crypto.webcrypto});w.print=()=>{};w.alert=m=>{throw Error(m);};
w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new w.Event('close'));};
w.addEventListener('error',e=>errors.push(e.error));
w.fetch=async(url,options={})=>{const headers=new Headers(options.headers);headers.set('Origin','http://127.0.0.1:5173');if(cookie)headers.set('Cookie',cookie);const response=await fetch(url,{...options,headers});for(const set of response.headers.getSetCookie())cookie=set.split(';')[0];return response;};
const $=s=>{const n=w.document.querySelector(s);assert.ok(n,s);return n;};
const set=(s,value)=>{$(s).value=value;$(s).dispatchEvent(new w.Event('input',{bubbles:true}));};
const wait=async(condition,label)=>{for(let i=0;i<100;i++){if(condition())return;await new Promise(r=>setTimeout(r,50));}throw Error('Tiempo agotado: '+label+' | '+w.document.querySelector('#extra-page')?.textContent?.slice(0,500));};
const route=async(hash)=>{w.location.hash=hash;await new Promise(r=>setTimeout(r,70));};
const submit=s=>$(s).dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
async function signIn(mail,pass){await route('#acceso');set('#access-email',mail);set('#access-password',pass);submit('#access-form');await wait(()=>w.location.hash!=='#acceso','inicio de sesión');}
async function signOut(){ $('#server-signout').click();await wait(()=>w.location.hash==='#inicio','cerrar sesión');}
try{
  w.eval(bundle.outputFiles[0].text);w.startBackend(base,undefined,true);
  await wait(()=>w.document.querySelector(`[data-api-add="${product.id}"]`),'cargar catálogo');
  await route('#registro');set('#register-name','Cliente de recorrido');set('#register-email',email);set('#register-password',password);set('#register-confirm',password);submit('#register-form');await wait(()=>w.location.hash==='#pedidos','registro');
  await route('#catalogo');await wait(()=>w.document.querySelector(`[data-api-add="${product.id}"]`),'catálogo autenticado');$(`[data-api-add="${product.id}"]`).click();await wait(()=>$('#cart-count').textContent==='1','agregar');
  await route('#carrito');$('#checkout-button').click();await wait(()=>w.location.hash==='#checkout','revisión');$('#demo-purchase').click();await wait(()=>w.document.querySelector('#server-delivery-form'),'entrega');submit('#server-delivery-form');await wait(()=>w.document.querySelector('#server-purchase-form button')&&!$('#server-purchase-form button').disabled,'cotización');
  assert.match($('#server-quote').textContent,/200.00/);set('#server-coupon','BEIGE10');$('#server-coupon').dispatchEvent(new w.Event('change',{bubbles:true}));await wait(()=>$('#server-quote').textContent.includes('180.00'),'descuento servidor');$('#server-purchase-form [name="ack"]').checked=true;submit('#server-purchase-form');await wait(()=>w.location.hash==='#compra/confirmacion','confirmación');assert.match($('#extra-page').textContent,/pendiente/);assert.equal($('#cart-count').textContent,'0');
  await route('#pedidos');await wait(()=>w.document.querySelector('[data-server-order]'),'mis pedidos');const orderId=$('[data-server-order]').dataset.serverOrder;$('[data-server-order]').click();await wait(()=>$('#order-detail').open,'ticket cliente');assert.match($('.order-ticket').textContent,/Bolsa de recorrido E2E/);$('[data-order-close]').click();
  await signOut();await signIn(process.env.BAGSTORE_TEST_ADMIN_EMAIL,process.env.BAGSTORE_TEST_ADMIN_PASSWORD);await route('#admin/reportes');await wait(()=>w.document.querySelector(`[data-server-order="${orderId}"]`),'reportes');$(`[data-server-order="${orderId}"]`).click();await wait(()=>$('#order-detail').open,'ticket administrador');
  for(const status of ['preparando','listo','entregado']){set('#server-order-status',status);if(status==='entregado')$('#order-server-update [name="confirm_payment"]').checked=true;submit('#order-server-update');await wait(()=>$('#order-server-message').textContent.includes('guardado'),'seguimiento '+status);}
  $('[data-order-close]').click();await route('#admin/existencias');await wait(()=>w.document.querySelector(`.server-stock-form[data-product="${product.id}"]`),'inventario');set(`#stock-n-${product.id}`,'8');set(`#stock-r-${product.id}`,'Recuento de recorrido E2E');submit(`.server-stock-form[data-product="${product.id}"]`);await wait(()=>$('#backend-workspace').textContent.includes('Recuento de recorrido E2E'),'historial');
  await signOut();await signIn(email,password);await route('#devoluciones');await wait(()=>w.document.querySelector('#server-return-form'),'devoluciones');set('#return-order',orderId);$('#return-order').dispatchEvent(new w.Event('change',{bubbles:true}));set('#return-product',String(product.id));set('#return-comment','Solicitud de recorrido completo');submit('#server-return-form');await wait(()=>$('#extra-page').textContent.includes('Solicitada'),'solicitud persistida');
  await route('#producto/'+product.id);await wait(()=>w.document.querySelector('#server-review-form'),'reseñas');set('#server-comment','Una bolsa muy práctica y bonita');submit('#server-review-form');await wait(()=>$('#server-reviews').textContent.includes('Una bolsa muy práctica y bonita'),'reseña persistida');
  assert.deepEqual(errors,[]);console.log(JSON.stringify({registro:true,login:true,carrito:true,cotizacionServidor:true,pedido:true,ticket:true,reportes:true,pagoManual:true,entrega:true,inventario:true,devolucion:true,resena:true,erroresDOM:errors.length}));
}finally{dom.window.close();}
