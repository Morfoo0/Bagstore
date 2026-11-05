import { ApiClient, ApiError } from '../services/api';
import { BackendCatalog, httpImage } from '../services/backend-catalog';
import type { CategoryDTO, CollectionDTO, ProductDTO, ProductSummary, ImageDTO, Page } from '../services/backend-catalog';
import { products } from '../data/products';
import { createCommerceRepository } from '../services/commerce';
import { createCatalogRepository } from '../services/catalogs';
import { requireCustomerAccess } from '../services/auth';
import { setupAccess } from './access';
import { createCart } from './cart';
import { bagArt } from './bag';
import { element as $, escapeHtml as h, money } from '../ui';
import '../backend.css';

const pendingPermission = 'Las escrituras requieren una sesión administrativa verificada. El backend todavía no ofrece autenticación; no se enviaron cambios.';
/** El proveedor de permisos se conectará a la sesión verificada del servidor, nunca a localStorage. */
export function setupBackendApp(baseUrl: string, verifiedAdmin: () => boolean = () => false) {
  const api = new BackendCatalog(new ApiClient(baseUrl));
  const summaries = new Map<number, ProductSummary>();
  const details = new Map<number, ProductDTO>();
  let categories: CategoryDTO[] = [];
  let publicPage = 1;
  let publicCategory = '';
  let publicCollection = '';
  let search = '';
  let publicOrder = 'reciente';
  let publicVersion = 0;
  let routeVersion = 0;
  let catalogReady = false;
  let currentCollection: CollectionDTO | undefined;
  const message = (s: string) => { $('#toast').textContent = s; $('#toast').classList.add('visible'); setTimeout(() => $('#toast').classList.remove('visible'), 3500); };
  const publish = (p: ProductDTO) => {
    details.set(p.id, p);
    const view = {id:p.id, name:p.nombre, category:p.categoria.nombre, categoryId:String(p.categoria.id), price:p.precio, label:'Color no especificado', color:'#CDB89E', accent:'#948067', imageData:p.imagen_principal?.url};
    const index = products.findIndex(v => v.id === p.id); if (index < 0) products.push(view); else products[index] = view;
    window.dispatchEvent(new Event('bagstore-products-changed'));
  };
  // Fuente API: no conservar productos/stock de la demostración ni reutilizar su carrito.
  products.splice(0);
  const commerce = {...createCommerceRepository(), quantity: (id: number) => details.get(id)?.existencias ?? 0};
  setupAccess(createCatalogRepository(), false);
  const savedIds: number[] = [];
  try { const entries: unknown = JSON.parse(localStorage.getItem('bagstore.api-cart.v1') ?? '[]'); if (Array.isArray(entries)) for (const entry of entries) if (Array.isArray(entry) && Number.isSafeInteger(entry[0]) && entry[0] > 0) savedIds.push(entry[0]); } catch { /* Cart informa recuperación. */ }
  let cart: ReturnType<typeof createCart> | undefined;
  const extra = document.createElement('section'); extra.id = 'extra-page'; extra.className = 'extra-page wrap'; extra.hidden = true; $('main').prepend(extra);
  // Mantener título y aviso del panel, reemplazando exclusivamente las vistas locales.
  document.querySelectorAll('[data-admin-section]').forEach(node => node.remove());
  const admin = document.createElement('section'); admin.className = 'admin-card'; admin.id = 'backend-workspace'; $('.admin-content').append(admin);
  $('.admin-notice').textContent = 'Catálogo conectado a la API. Consulta pública disponible; las escrituras esperan autenticación administrativa.';
  $('.admin-sidebar-bottom p').textContent = 'La API conserva datos temporalmente en memoria. Reiniciar el servidor elimina los cambios.';
  $('.announcement span').textContent = 'CATÁLOGO API · COMPRAS NO DISPONIBLES';
  $('#year').textContent = String(new Date().getFullYear());
  $('#hero-bag').innerHTML = bagArt({id:0,category:'Tote',color:'#CDB89E',accent:'#948067'}, 'api-hero');
  const colorSelect = $<HTMLSelectElement>('#public-color-filter'); colorSelect.disabled = true; colorSelect.innerHTML = '<option>Colores: pendientes de API</option>';
  $('#catalogo .filters').innerHTML = '<button class="filter active" data-api-category="">Todas</button>';
  $('#catalogo .catalog-controls').insertAdjacentHTML('beforeend', '<label class="api-sort">Ordenar por<select id="api-sort"><option value="reciente">Más recientes</option><option value="nombre_asc">Nombre A–Z</option><option value="nombre_desc">Nombre Z–A</option><option value="precio_asc">Precio: menor a mayor</option><option value="precio_desc">Precio: mayor a menor</option></select></label>');
  const pagination = document.createElement('div'); pagination.className = 'api-pagination'; $('#products').after(pagination);
  const collections = document.createElement('section'); collections.id = 'api-collections'; collections.className = 'collection-showcase wrap'; $('#colecciones').after(collections);
  // Promociones y regalo necesitan contrato de pedidos: no calcular beneficios locales con API.
  $('.coupon-details').hidden = true; $('.gift-box').hidden = true;
  $('#cart-storage-note').textContent = 'La disponibilidad se comprueba con el catálogo. Los pedidos aún no están habilitados.';
  const art = (p: ProductSummary) => p.imagen_principal ? `<img src="${h(p.imagen_principal.url)}" alt="${h(p.imagen_principal.texto_alternativo || p.nombre)}" loading="lazy"/>` : `<span class="api-no-image">Imagen no disponible</span>`;
  const errorText = (error: unknown) => error instanceof Error ? error.message : 'No pudimos cargar los datos. Inténtalo nuevamente.';
  const errorMarkup = (error: unknown) => `<p role="alert" class="field-error">${h(errorText(error))}</p><button type="button" class="product-secondary" data-api-retry>Reintentar</button>`;
  function pager(p: Pick<Page<unknown>, 'paginacion'>, target: string) { return `<button class="product-secondary" data-page-target="${target}" data-page="${p.paginacion.pagina-1}" ${p.paginacion.pagina <= 1?'disabled':''}>Anterior</button><span>Página ${p.paginacion.pagina} de ${Math.max(1,p.paginacion.total_paginas)} · ${p.paginacion.total} resultados</span><button class="product-secondary" data-page-target="${target}" data-page="${p.paginacion.pagina+1}" ${p.paginacion.pagina >= p.paginacion.total_paginas?'disabled':''}>Siguiente</button>`; }
  async function allCategories() {
    let page = 1; let result: CategoryDTO[] = [];
    do { const data = await api.categories({pagina:page,por_pagina:100}); result.push(...data.datos); if (page >= data.paginacion.total_paginas) break; page++; if (page > 1000) throw new ApiError('El catálogo de categorías es demasiado grande.'); } while (true);
    categories = result; const select = $<HTMLSelectElement>('#public-category-filter'); select.replaceChildren(new Option('Todas',''),...categories.map(c => new Option(c.nombre,String(c.id)))); select.value = publicCategory;
    $('#catalogo .filters').innerHTML = `<button class="filter ${!publicCategory?'active':''}" data-api-category="">Todas</button>` + categories.map(c=>`<button class="filter ${publicCategory===String(c.id)?'active':''}" data-api-category="${c.id}">${h(c.nombre)}</button>`).join('');
  }
  async function loadPublic() {
    const version = ++publicVersion; $('#products').innerHTML = '<p role="status">Cargando bolsas…</p>'; $('#empty').hidden = true; pagination.innerHTML = ''; $('#catalogo').setAttribute('aria-busy','true');
    try {
      const data = await api.products({pagina:publicPage,por_pagina:12,nombre:search,categoria_id:publicCategory || undefined,coleccion_id:publicCollection || undefined,orden:publicOrder});
    if (version !== publicVersion) return;
      data.datos.forEach(p=>summaries.set(p.id,p));
      $('#products').innerHTML = data.datos.map(p=>`<article class="product-card"><a href="#producto/${p.id}" class="product-image product-image-link">${art(p)}</a><div class="product-meta"><h3><a href="#producto/${p.id}">${h(p.nombre)}</a></h3><p>${money(p.precio)} MXN · ${h(p.categoria.nombre)}</p></div><button class="add-button" data-api-add="${p.id}" ${!p.disponible?'disabled':''}>${p.disponible?'Agregar a mi bolsa':'Agotado'}</button></article>`).join('');
      $('#empty').hidden = data.datos.length > 0; $('#results').textContent = `${data.paginacion.total} bolsas${currentCollection ? ' · '+currentCollection.nombre : ''}`; pagination.innerHTML = pager(data,'public');
    } catch(error) { if (version === publicVersion) { $('#products').innerHTML = errorMarkup(error); $('#results').textContent = 'No se pudo cargar el catálogo.'; } }
    finally { if (version === publicVersion) $('#catalogo').removeAttribute('aria-busy'); }
  }
  async function loadCollections(page = 1) {
    collections.innerHTML = '<p role="status">Cargando colecciones…</p>';
    try { const data = await api.collections({pagina:page,por_pagina:12}); collections.innerHTML = `<h2>Nuestras colecciones</h2><div class="collection-tile-grid">${data.datos.map(c=>`<article class="collection-tile"><a href="#coleccion/${c.id}">${c.imagen_portada_url?`<img class="api-cover" src="${h(c.imagen_portada_url)}" alt="${h(c.nombre)}"/>`:''}<h3>${h(c.nombre)}</h3></a><p>${h(c.descripcion || '')}</p><span>${c.total_productos} productos</span></article>`).join('') || '<p>No hay colecciones disponibles.</p>'}</div><div class="api-pagination">${pager(data,'collections')}</div>`; }
    catch(error) { collections.innerHTML = errorMarkup(error); }
  }
  async function add(id: number, button: HTMLButtonElement) {
    button.disabled = true;
    try { const p = await api.product(id); publish(p); cart?.add(id); }
    catch(error) { message(errorText(error)); }
    finally { button.disabled = summaries.get(id)?.disponible === false || details.get(id)?.existencias === 0; }
  }
  const editor = document.createElement('dialog'); editor.className = 'api-editor'; editor.setAttribute('aria-labelledby','api-editor-title'); document.body.append(editor);
  let editingResource: 'productos'|'categorias'|'colecciones' = 'productos';
  let editingId: number | undefined;
  let originalProduct: ProductDTO | undefined;
  let selectableProducts: ProductSummary[] = [];
  let editorOpener: HTMLElement | null = null;
  const field = (name: string, label: string, value: string|number = '', attrs = '') => `<label for="api-${name}">${label}</label><input id="api-${name}" name="${name}" value="${h(String(value))}" ${attrs}/><p class="field-error" data-api-error="${name}" role="alert"></p>`;
  const stateField = (state = 'activo') => `<label for="api-estado">Estado</label><select id="api-estado" name="estado"><option value="activo" ${state==='activo'?'selected':''}>Activo</option><option value="inactivo" ${state==='inactivo'?'selected':''}>Inactivo</option></select>`;
  async function openEditor(resource: typeof editingResource, id?: number) {
    editingResource = resource; editingId = id; originalProduct = undefined; editorOpener = document.activeElement as HTMLElement;
    editor.innerHTML = '<p role="status">Cargando formulario…</p>'; editor.showModal();
    try {
      let body = ''; let title = '';
      if (resource === 'productos') {
        const p = id ? await api.product(id) : undefined; originalProduct = p; if (!categories.length) await allCategories();
        title = id?'Editar producto':'Nuevo producto';
        body = field('nombre','Nombre',p?.nombre,'required minlength="2" maxlength="150"') + field('sku','SKU',p?.sku,'required minlength="3" maxlength="50" pattern="[A-Z0-9]+(-[A-Z0-9]+)*" '+(id?'readonly':'')) + `<label for="api-descripcion">Descripción</label><textarea id="api-descripcion" name="descripcion" maxlength="5000" rows="4">${h(p?.descripcion || '')}</textarea>` + field('precio','Precio MXN',p?.precio ?? '', 'type="number" min="0.01" max="999999.99" step="0.01" required') + `<label for="api-categoria_id">Categoría</label><select id="api-categoria_id" name="categoria_id" required><option value="">Selecciona una categoría</option>${categories.map(c=>`<option value="${c.id}" ${p?.categoria.id===c.id?'selected':''}>${h(c.nombre)}</option>`).join('')}</select><p class="field-error" data-api-error="categoria_id" role="alert"></p>` + field('existencias','Existencias',p?.existencias ?? 0,'type="number" min="0" max="1000000" step="1" required') + stateField(p?.estado) + '<p class="demo-note">El SKU no cambia al editar. Colores y carga de archivos esperan soporte del backend. Puedes preparar imágenes por URL HTTP(S).</p><fieldset><legend>Imágenes del producto · máximo 10</legend><div id="api-image-rows"></div><button type="button" id="api-image-add" class="product-secondary">Agregar imagen por URL</button><p class="field-error" data-api-error="imagenes" role="alert"></p></fieldset>';
      } else if (resource === 'categorias') {
        const c = id ? await api.category(id) : undefined; title = id?'Editar categoría':'Nueva categoría';
        body = field('nombre','Nombre',c?.nombre,'required minlength="2" maxlength="80"') + `<label for="api-descripcion">Descripción</label><textarea id="api-descripcion" name="descripcion" maxlength="1000">${h(c?.descripcion || '')}</textarea>` + field('orden','Orden',c?.orden??0,'type="number" min="0" step="1" required') + stateField(c?.estado);
      } else {
        const c = id ? await api.collection(id) : undefined; title = id?'Editar colección':'Nueva colección';
        selectableProducts = [];
        if (!id) {
          let memberPage = 1;
          while (true) {
            const result = await api.products({pagina:memberPage,por_pagina:100}); selectableProducts.push(...result.datos);
            if(memberPage >= result.paginacion.total_paginas) break;
            if(++memberPage > 1000) throw new ApiError('Hay demasiados productos para este selector.');
          }
        }
        // GET actual no permite recuperar miembros inactivos: nunca reemplazar relaciones incompletas.
        body = field('nombre','Nombre',c?.nombre,'required minlength="2" maxlength="100"') + `<label for="api-descripcion">Descripción</label><textarea id="api-descripcion" name="descripcion" maxlength="2000">${h(c?.descripcion || '')}</textarea>` + field('imagen_portada_url','URL de portada',c?.imagen_portada_url??'','type="url" maxlength="500"') + stateField(c?.estado) + `<fieldset><legend>Productos de la colección</legend>${id ? '<p>La selección actual aún no puede recuperarse de forma completa. La edición de esta colección está temporalmente deshabilitada.</p>' : '<div class="checkbox-grid">'+selectableProducts.map(p=>'<label><input type="checkbox" name="producto_ids" value="'+p.id+'"/> '+h(p.nombre)+'</label>').join('')+'</div>'}<p class="field-error" data-api-error="producto_ids" role="alert"></p></fieldset>`;
      }
      if (!editor.open) return;
      const incompleteMembership = resource === 'colecciones' && id !== undefined;
      editor.innerHTML = `<div class="ticket-toolbar"><h2 id="api-editor-title">${title}</h2><button type="button" class="product-secondary" data-editor-close>Cerrar</button></div><form id="api-write-form" class="feature-form">${body}<p class="access-feedback" id="api-write-status" role="status">${verifiedAdmin() ? incompleteMembership ? 'Edición bloqueada: falta membresía administrativa completa en la respuesta de colección.' : 'Revisa los campos antes de guardar.' : pendingPermission}</p><button class="button" type="submit" ${!verifiedAdmin() || incompleteMembership ? 'disabled' : ''}>${verifiedAdmin() ? 'Guardar cambios' : 'Guardar · requiere acceso administrativo'}</button></form>`;
      if (resource === 'productos') for (const img of originalProduct?.imagenes ?? []) addImage(img);
      editor.querySelector<HTMLElement>('input')?.focus();
    } catch(error) { editor.innerHTML = `<h2 id="api-editor-title">No se pudo abrir el formulario</h2>${errorMarkup(error)}<button class="product-secondary" data-editor-close>Cerrar</button>`; }
  }
  let imageSequence = 0;
  function addImage(img?: ImageDTO) {
    const container = editor.querySelector('#api-image-rows')!;
    if (container.children.length >= 10) return;
    const n = ++imageSequence;
    const row = document.createElement('div'); row.className = 'api-image-row';
    row.innerHTML = `<label for="api-image-url-${n}">URL de imagen</label><input id="api-image-url-${n}" data-img-url type="url" maxlength="500" required value="${h(img?.url??'')}"/><label for="api-image-alt-${n}">Texto alternativo</label><input id="api-image-alt-${n}" data-img-alt maxlength="150" value="${h(img?.texto_alternativo??'')}"/><label for="api-image-order-${n}">Orden</label><input id="api-image-order-${n}" data-img-order type="number" min="0" step="1" required value="${img?.orden??container.children.length+1}"/><label><input data-img-main type="checkbox" ${img?.es_principal?'checked':''}/> Imagen principal</label><button type="button" class="product-secondary" data-image-remove>Quitar imagen</button>`;
    container.append(row);
  }
  editor.addEventListener('click',event=>{const b=(event.target as HTMLElement).closest('button'); if(b?.hasAttribute('data-editor-close'))editor.close(); if(b?.id==='api-image-add')addImage(); if(b?.hasAttribute('data-image-remove'))b.closest('.api-image-row')?.remove(); if(b?.hasAttribute('data-api-retry')){editor.close(); void openEditor(editingResource,editingId);} });
  editor.addEventListener('close',()=>editorOpener?.isConnected && editorOpener.focus());
  editor.addEventListener('submit',async event=>{
    event.preventDefault(); const form = event.target as HTMLFormElement; if (!form.reportValidity()) return;
    const status = $('#api-write-status');
    if (!verifiedAdmin()) { status.textContent = pendingPermission; return; }
    if (editingResource === 'colecciones' && editingId !== undefined) { status.textContent = 'Falta recuperar la membresía administrativa completa. No se enviaron cambios.'; return; }
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]')!;
    const data = new FormData(form); const value = (key: string) => String(data.get(key) ?? '').trim();
    form.querySelectorAll<HTMLElement>('[data-api-error]').forEach(e=>e.textContent='');
    form.querySelectorAll('[aria-invalid]').forEach(e=>e.removeAttribute('aria-invalid'));
    submit.disabled=true; form.setAttribute('aria-busy','true'); status.textContent='Guardando cambios…';
    try {
      const estado = value('estado') as 'activo'|'inactivo';
      if(editingResource==='productos') {
        const images: ImageDTO[] = [...form.querySelectorAll('.api-image-row')].map(row=>({url:row.querySelector<HTMLInputElement>('[data-img-url]')!.value.trim(), texto_alternativo:row.querySelector<HTMLInputElement>('[data-img-alt]')!.value.trim() || null, orden:Number(row.querySelector<HTMLInputElement>('[data-img-order]')!.value), es_principal:row.querySelector<HTMLInputElement>('[data-img-main]')!.checked}));
        await api.saveProduct({nombre:value('nombre'),descripcion:value('descripcion')||null,precio:Number(value('precio')),sku:value('sku').toUpperCase(),categoria_id:Number(value('categoria_id')),existencias:Number(value('existencias')),estado,imagenes:images},editingId);
      } else if(editingResource==='categorias') await api.saveCategory({nombre:value('nombre'),descripcion:value('descripcion')||null,orden:Number(value('orden')),estado},editingId);
      else {
        const ids = data.getAll('producto_ids').map(v=>Number(v));
        if(ids.some(id=>!Number.isSafeInteger(id)||id<=0)||ids.length>200)throw new ApiError('Selecciona hasta 200 productos válidos para la colección.');
        if(value('imagen_portada_url')&&!httpImage(value('imagen_portada_url')))throw new ApiError('La portada debe ser una URL HTTP o HTTPS.');
        await api.saveCollection({nombre:value('nombre'),descripcion:value('descripcion')||null,estado,imagen_portada_url:value('imagen_portada_url')||null,producto_ids:ids});
      }
      // Solo refrescar después de respuesta válida; no simular guardados locales.
      editor.close(); message('Cambios guardados en el servidor.'); await allCategories(); await loadCollections(); await loadPublic(); await renderAdmin(location.hash.split('/')[1]||'resumen');
    }catch(error){
      status.textContent=errorText(error)+(error instanceof ApiError && error.details.length ? ' '+error.details.map(d=>d.mensaje).join(' ') : '');
      if(error instanceof ApiError)for(const detail of error.details){
        // No insertar nombres de campos remotos en selectores CSS.
        const target=[...form.querySelectorAll<HTMLElement>('[data-api-error]')].find(e=>e.dataset.apiError===detail.campo || detail.campo.startsWith(e.dataset.apiError+'.'));
        if(target)target.textContent=detail.mensaje;
        const input=[...form.elements].find(e=>(e as HTMLInputElement).name===detail.campo); input?.setAttribute('aria-invalid','true');
      }
      status.focus();
    }finally{submit.disabled=!verifiedAdmin();form.removeAttribute('aria-busy');}
  });
  async function renderAdmin(section: string, page = 1) {
    const version = ++routeVersion; admin.innerHTML = '<p role="status">Cargando datos del servidor…</p>'; admin.setAttribute('aria-busy','true');
    try {
      let markup = '';
      if (section === 'productos' || section === 'existencias') {
        const data = await api.products({pagina:page,por_pagina:20}); data.datos.forEach(p=>summaries.set(p.id,p));
        markup = `<div class="admin-card-heading"><h2>${section==='existencias'?'Existencias del catálogo':'Productos'}</h2><button class="product-secondary" data-api-new="productos">Preparar nuevo producto</button></div><p class="demo-note">Se muestran productos activos. Consultar inactivos, guardar cambios y ajustar stock requiere autorización del backend. Abre un producto para consultar sus existencias y preparar los campos.</p><div class="admin-table-scroll"><table class="admin-table"><thead><tr><th>Producto</th><th>Categoría</th><th>Precio</th><th>Disponibilidad</th><th>Acciones</th></tr></thead><tbody>${data.datos.map(p=>`<tr><td>${h(p.nombre)}</td><td>${h(p.categoria.nombre)}</td><td>${money(p.precio)}</td><td>${p.disponible?'Disponible':'Agotado'}</td><td><button class="product-secondary" data-api-edit="productos" data-id="${p.id}">Ver / preparar edición</button></td></tr>`).join('') || '<tr><td colspan="5">No hay productos activos.</td></tr>'}</tbody></table></div><div class="api-pagination">${pager(data,'admin')}</div>`;
      } else if (section === 'categorias' || section === 'colecciones') {
        const data = section==='categorias'? await api.categories({pagina:page,por_pagina:20}) : await api.collections({pagina:page,por_pagina:20});
        markup = `<div class="admin-card-heading"><h2>${section==='categorias'?'Categorías':'Colecciones'}</h2><button class="product-secondary" data-api-new="${section}">Preparar ${section==='categorias'?'categoría':'colección'}</button></div><p class="demo-note">Consulta activa de la API. Edición, estados y eliminación esperan acceso administrativo. El borrado de categorías/colecciones es definitivo; categorías con productos devuelven conflicto.</p><div class="collection-tile-grid">${data.datos.map(c=>`<article class="feature-card"><h3>${h(c.nombre)}</h3><p>${h(c.descripcion||'')}</p><p>${c.total_productos} productos · ${h(c.slug)}</p><button class="product-secondary" data-api-edit="${section}" data-id="${c.id}">Ver / preparar edición</button></article>`).join('') || '<p>No hay resultados.</p>'}</div><div class="api-pagination">${pager(data,'admin')}</div>`;
      } else if (section === 'resumen') markup = `<h2>Catálogo conectado</h2><p>Productos, categorías y colecciones se consultan en la API del equipo. Los cambios del servidor se reflejan al actualizar.</p><p>Las cuentas, pedidos, pagos, reportes, reseñas y devoluciones aún necesitan endpoints.</p><a class="button" href="#admin/productos">Consultar productos</a>`;
      else if (section === 'conexion') { await api.health(); markup = '<h2>Conexión disponible</h2><p>El endpoint /api/health respondió JSON. Esto no acredita una sesión ni permisos administrativos.</p>'; }
      else markup = '<h2>Servicio pendiente de integración</h2><p>El backend actual solo ofrece catálogo. Esta sección se habilitará cuando existan los endpoints y permisos correspondientes.</p>';
      if(version===routeVersion)admin.innerHTML = markup;
    } catch(error) { if(version===routeVersion)admin.innerHTML = errorMarkup(error); }
    finally { if(version===routeVersion)admin.removeAttribute('aria-busy'); }
  }
  async function route() {
    if (editor.open) editor.close();
    const hash = location.hash; const version = ++routeVersion;
    if(hash.startsWith('#compra/')) { requireCustomerAccess(); return; }
    if(hash.startsWith('#admin')) { extra.hidden = true; await renderAdmin(hash.split('/')[1] || 'resumen'); return; }
    if(hash==='#acceso'||hash==='#registro'){extra.hidden=true;return;}
    const productMatch = /^#producto\/(\d+)$/.exec(hash); const collectionMatch = /^#coleccion\/(\d+)$/.exec(hash);
    if(productMatch || ['#devoluciones','#portafolio'].includes(hash)) {
      for(const child of $('main').children)if(child instanceof HTMLElement)child.hidden=child!==extra;
      extra.hidden = false; extra.innerHTML = '<p role="status">Cargando…</p>';
      try {
        if(productMatch){const p=await api.product(Number(productMatch[1]));if(version!==routeVersion)return;publish(p);extra.innerHTML=`<a href="#catalogo" class="continue-shopping">← Volver al catálogo</a><div class="detail-grid"><div class="detail-art">${art(p)}${p.imagenes.length>1?`<div class="api-gallery">${p.imagenes.slice().sort((a,b)=>a.orden-b.orden).map(i=>`<img src="${h(i.url)}" alt="${h(i.texto_alternativo||p.nombre)}"/>`).join('')}</div>`:''}</div><div><p class="eyebrow">${h(p.categoria.nombre)}</p><h1 tabindex="-1">${h(p.nombre)}</h1><p>SKU: ${h(p.sku)}</p><p class="detail-price">${money(p.precio)} MXN</p><p class="api-description">${h(p.descripcion||'')}</p><p>${p.existencias} unidades disponibles</p><button class="button" data-api-add="${p.id}" ${p.disponible?'':'disabled'}>${p.disponible?'Agregar a mi bolsa':'Agotado'}</button><button class="product-secondary" data-api-share="${p.id}">Copiar enlace</button><p class="demo-note">Los colores y las reseñas se incorporarán cuando estén disponibles en la API.</p></div></div>`;}
        else if(hash==='#portafolio'){extra.innerHTML='<h1>Nuestras colecciones</h1><a href="#colecciones" class="button">Explorar colecciones</a>';}
        else extra.innerHTML='<h1>Cambios y devoluciones</h1><p>Para consultar y gestionar devoluciones necesitamos el servicio de pedidos y una cuenta verificada. Esta función todavía no está disponible.</p><a href="#catalogo" class="button">Volver al catálogo</a>';
      }catch(error){if(version===routeVersion)extra.innerHTML=errorMarkup(error);}
      extra.querySelector<HTMLElement>('h1')?.focus();return;
    }
    extra.hidden=true;
    if(collectionMatch){try {const c=await api.collection(Number(collectionMatch[1]));if(version!==routeVersion)return; currentCollection=c;publicCollection=String(c.id); publicPage=1;location.hash='catalogo';}catch(error){message(errorText(error));}return;}
    if(hash==='#catalogo')await loadPublic();
    if(hash==='#colecciones')await loadCollections();
  }
  document.addEventListener('click',event=>{
    const button=(event.target as HTMLElement).closest<HTMLButtonElement>('button'); const link=(event.target as HTMLElement).closest<HTMLAnchorElement>('[data-category]');
    if(link){const term=link.dataset.category;const c=categories.find(c=>c.slug.includes(term==='Tote'?'tote':term==='Crossbody'?'cross':term==='Mini'?'mini':'___'));publicCategory=c?String(c.id):'';publicCollection='';currentCollection=undefined;publicPage=1;$<HTMLSelectElement>('#public-category-filter').value=publicCategory;void loadPublic();}
    if(!button)return;
    if(button.dataset.apiAdd)void add(Number(button.dataset.apiAdd),button);
    if(button.hasAttribute('data-api-category')){publicCategory=button.dataset.apiCategory!;publicCollection='';currentCollection=undefined;publicPage=1;$<HTMLSelectElement>('#public-category-filter').value=publicCategory;void loadPublic();}
    if(button.dataset.pageTarget){const n=Number(button.dataset.page);if(n<1)return;if(button.dataset.pageTarget==='public'){publicPage=n;void loadPublic();}else if(button.dataset.pageTarget==='collections')void loadCollections(n);else void renderAdmin(location.hash.split('/')[1]||'resumen',n);}
    if(button.dataset.apiNew)void openEditor(button.dataset.apiNew as typeof editingResource);
    if(button.dataset.apiEdit)void openEditor(button.dataset.apiEdit as typeof editingResource,Number(button.dataset.id));
    if(button.hasAttribute('data-api-retry')&&!editor.contains(button)){if(!catalogReady){void boot();return;}if(collections.contains(button))void loadCollections();else if(admin.contains(button))void renderAdmin(location.hash.split('/')[1]||'resumen');else if(extra.contains(button))void route();else void loadPublic();}
    if(button.dataset.apiShare){const url=new URL(location.href);url.hash=`producto/${button.dataset.apiShare}`;void navigator.clipboard?.writeText(url.href).then(()=>message('Enlace copiado.')).catch(()=>message('No se pudo copiar. Copia el enlace desde la barra del navegador.'));}
  });
  $('#search').addEventListener('submit',event=>{event.preventDefault();search=$<HTMLInputElement>('#search-input').value.trim();publicPage=1;location.hash='catalogo';void loadPublic();});
  $('#clear-search').addEventListener('click',()=>{search='';publicCategory='';publicCollection='';currentCollection=undefined;publicPage=1;$<HTMLInputElement>('#search-input').value='';$<HTMLSelectElement>('#public-category-filter').value='';void loadPublic();});
  $('#public-category-filter').addEventListener('change',event=>{publicCategory=(event.target as HTMLSelectElement).value;publicPage=1;void loadPublic();});
  $('#api-sort').addEventListener('change',event=>{publicOrder=(event.target as HTMLSelectElement).value;publicPage=1;void loadPublic();});
  $('#menu-toggle').addEventListener('click',()=>{const open=$('#navigation').classList.toggle('open');$('#menu-toggle').setAttribute('aria-expanded',String(open));$('#menu-toggle').setAttribute('aria-label',open?'Cerrar menú':'Abrir menú');});
  $('#navigation').addEventListener('click',()=>{$('#navigation').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'){$('#navigation').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');}});
  $('#returns-info').addEventListener('click',()=>{location.hash='devoluciones';});
  window.addEventListener('hashchange',()=>{void route();});
  async function boot() {
    $('#cart-open').setAttribute('disabled','');
    try {
      // Restaurar solo IDs del carrito API; no importar datos de demostración.
      const saved = await Promise.allSettled([...new Set(savedIds)].map(async id=>publish(await api.product(id))));
      const unresolved = saved.some(r=>r.status==='rejected' && (!(r.reason instanceof ApiError) || r.reason.status!==404));
      if(unresolved)throw new ApiError('No pudimos verificar tu carrito guardado. Reintenta sin cerrar esta página.');
      cart=createCart(message,commerce,'bagstore.api-cart.v1'); catalogReady=true; $('#cart-open').removeAttribute('disabled');
      await Promise.allSettled([allCategories().catch(error=>{message('Categorías: '+errorText(error));}),loadPublic(),loadCollections()]);
      await route();
    }catch(error){$('#products').innerHTML=errorMarkup(error); message(errorText(error));}
  }
  // Solo usado para reintentar restauración sin borrar un carrito por error de red.
  $('#cart-open').addEventListener('click',()=>{if(!catalogReady)void boot();});
  void boot();
}
