import { setupOrderDetails } from './order-details';
import { requireCustomerAccess } from '../services/auth';
import { products } from '../data/products';
import { bagArt } from './bag';
import { element as $, escapeHtml as h, money } from '../ui';
import type { Product } from '../types/product';
import type { CommerceRepository, DemoOrder } from '../services/commerce';
import { csvCell } from '../services/commerce';
import type { CatalogRepository } from '../services/catalogs';
import type { createCart } from './cart';
import { ApiClient } from '../services/api';

const visual = (p: Product, prefix: string) => p.imageData ? `<img src="${p.imageData}" alt="${h(p.name)}"/>` : bagArt(p, prefix);
const day = (value: string) => new Date(value).toLocaleDateString('en-CA');
const when = (value: string) => new Date(value).toLocaleString('es-MX');
const table = (head: string[], bodyId: string) => `<div class="admin-table-scroll" tabindex="0" role="region" aria-label="Tabla desplazable"><table class="admin-table"><thead><tr>${head.map(c => `<th scope="col">${c}</th>`).join('')}</tr></thead><tbody id="${bodyId}"></tbody></table></div>`;

export function setupFeatures(commerce: CommerceRepository, _catalogs: CatalogRepository, cart: ReturnType<typeof createCart>, notify: (s: string) => void) {
  const orderDetails = setupOrderDetails(commerce);
  const extra = document.createElement('section'); extra.id = 'extra-page'; extra.hidden = true; extra.className = 'extra-page wrap';
  $('main').prepend(extra);
  const collectionGrid = document.createElement('section'); collectionGrid.id = 'collection-showcase'; collectionGrid.className = 'collection-showcase wrap';
  $('#colecciones').after(collectionGrid);
  document.querySelectorAll('.product-sandbox-note').forEach(p => { p.textContent = 'Los productos activos y sus fotos aparecen en la tienda.'; });
  const adminNav = $('#admin-page .admin-sidebar nav');
  adminNav.insertAdjacentHTML('beforeend', '<a href="#admin/devoluciones" data-admin-link="devoluciones"><span aria-hidden="true">↶</span> Devoluciones</a><a href="#admin/conexion" data-admin-link="conexion"><span aria-hidden="true">⌁</span> Conexión API</a>');
  function panel(section: string, markup: string) {
    const target = document.querySelector<HTMLElement>(`[data-admin-section="${section}"]`);
    if (target) { target.className = ''; target.innerHTML = markup; }
    else { const node = document.createElement('section'); node.dataset.adminSection = section; node.hidden = true; node.innerHTML = markup; $('.admin-content').append(node); }
  }
  panel('colecciones', `<div class="admin-card"><div class="admin-card-heading"><h2>Gestionar colecciones</h2><button id="collection-new" class="button">+ Nueva colección</button></div><p class="demo-note">Organiza productos que comparten un estilo o una ocasión.</p><div id="collection-admin-list"></div><form id="collection-form" class="feature-form" hidden><h3 id="collection-form-title">Nueva colección</h3><label for="collection-name">Nombre</label><input id="collection-name" required minlength="2" maxlength="60"/><label for="collection-description">Descripción</label><textarea id="collection-description" maxlength="500" rows="3"></textarea><fieldset><legend>Productos asociados</legend><div id="collection-product-options" class="checkbox-grid"></div></fieldset><p id="collection-error" class="field-error" role="alert"></p><div class="feature-actions"><button class="button" type="submit">Guardar colección</button><button id="collection-cancel" class="product-secondary" type="button">Cancelar</button></div></form></div>`);
  panel('existencias', `<div class="admin-card"><h2>Inventario</h2><p class="demo-note">Cada producto comienza con 20 unidades ficticias hasta registrar un ajuste. Nunca representa stock real. Las compras de prueba descuentan unidades locales.</p><div class="feature-toolbar"><label>Buscar producto<input id="stock-search" type="search" placeholder="Nombre o categoría"/></label><label class="inline-check"><input id="stock-low" type="checkbox"/> Solo stock bajo (5 o menos)</label></div><p id="stock-message" role="status"></p>${table(['Producto', 'Estado', 'Existencias', 'Ajustar cantidad y motivo'], 'stock-body')}<h3 class="feature-spaced">Últimos movimientos</h3><ul id="stock-history" class="feature-history"></ul></div>`);
  panel('reportes', `<div class="admin-card"><div class="admin-card-heading"><h2>Reportes de ventas</h2><button id="report-export" class="product-secondary">Descargar CSV</button></div><p class="demo-note">Solo pedidos generados por el recorrido de prueba en este navegador. No son ventas reales.</p><div class="feature-toolbar"><label>Desde<input id="report-from" type="date"/></label><label>Hasta<input id="report-to" type="date"/></label><button id="report-clear" class="product-secondary">Limpiar fechas</button></div><p id="report-error" class="field-error" role="status"></p><div id="report-metrics" class="admin-stat-grid"></div>${table(['Pedido', 'Fecha', 'Unidades', 'Total', 'Acciones'], 'report-body')}</div>`);
  panel('devoluciones', `<div class="admin-card"><h2>Solicitudes de devolución</h2><p class="demo-note">Gestión local de solicitudes; no produce reembolsos ni cambios de inventario.</p><p id="admin-returns-message" role="status"></p>${table(['Solicitud / pedido', 'Producto', 'Motivo / descripción', 'Estado'], 'admin-returns-body')}</div>`);
  panel('conexion', `<div class="admin-card"><h2>Preparación de API</h2><p>El cliente HTTP está listo para <code>fetch()</code>, JSON, tiempo de espera y errores 401/403. Las rutas y respuestas definitivas deben acordarse con el equipo de Python.</p><p class="demo-note">Esta tienda sigue en modo demostración. No se envían productos, pedidos, contraseñas ni fotos a ningún servidor.</p><button id="api-check" class="button">Comprobar conexión configurada</button><p id="api-status" role="status"></p><p>Configura VITE_API_BASE_URL y VITE_API_HEALTH_PATH en un archivo .env local y reinicia Vite. Consulta docs/contrato-api-propuesto.md.</p></div>`);
  document.body.insertAdjacentHTML('beforeend', '<dialog id="feature-confirm" class="info-dialog" aria-labelledby="feature-confirm-title"><h2 id="feature-confirm-title">Cambiar estado de colección</h2><p id="feature-confirm-text"></p><div class="feature-actions"><button id="feature-confirm-cancel" class="product-secondary">Cancelar</button><button id="feature-confirm-ok" class="button">Confirmar cambio</button></div></dialog><dialog id="share-dialog" class="info-dialog" aria-labelledby="share-title"><h2 id="share-title">Compartir producto</h2><p>Este enlace solo funciona en esta computadora mientras el servidor local está encendido.</p><label for="share-url">Enlace</label><input id="share-url" type="text" readonly/><div class="feature-actions"><button id="share-copy" class="button">Copiar enlace</button><button id="share-close" class="product-secondary">Cerrar</button></div><p id="share-feedback" role="status"></p></dialog>');
  let editingCollection: string | undefined;
  let togglingCollection: string | undefined;
  let lastOrder: DemoOrder | undefined;
  let delivery = 'Recoger en tienda (demo)';
  let shipping = 0;
  let payment = 'Tarjeta de prueba';
  let placingOrder = false;
  function changed() { window.dispatchEvent(new Event('bagstore-commerce-changed')); renderCollections(); renderAdmin(); }
  function collectionsMarkup() {
    const visible = commerce.collections().filter(c => c.active);
    return visible.map(c => { const p = products.find(p => c.productIds.includes(p.id)); return `<article class="collection-tile"><a href="#coleccion/${c.id}"><div class="collection-tile-art">${p ? visual(p, `collection-${c.id}`) : '<span>◇</span>'}</div><h3>${h(c.name)}</h3></a><p>${h(c.description)}</p><a class="text-link" href="#coleccion/${c.id}">Ver colección →</a></article>`; }).join('') || '<p>No hay colecciones activas todavía.</p>';
  }
  function renderCollections() { collectionGrid.innerHTML = `<div class="section-heading"><h2>Encuentra tu colección.</h2><a href="#portafolio" class="text-link">Ver portafolio →</a></div><div class="collection-tile-grid">${collectionsMarkup()}</div>`; }
  function selectedOrders() {
    const from = $<HTMLInputElement>('#report-from').value; const to = $<HTMLInputElement>('#report-to').value;
    if (from && to && from > to) { $('#report-error').textContent = 'La fecha inicial debe ser anterior o igual a la final.'; return []; }
    $('#report-error').textContent = '';
    return commerce.orders().filter(o => (!from || day(o.date) >= from) && (!to || day(o.date) <= to));
  }
  function renderReports() {
    const orders = selectedOrders();
    const total = orders.reduce((n, o) => n + o.total, 0); const units = orders.reduce((n, o) => n + o.items.reduce((s, i) => s + i.qty, 0), 0);
    $('#report-metrics').innerHTML = `<article><span>PEDIDOS</span><strong>${orders.length}</strong></article><article><span>TOTAL CON ENVÍO</span><strong class="report-number">${money(total)}</strong></article><article><span>UNIDADES</span><strong>${units}</strong></article>`;
    $('#report-body').innerHTML = orders.map(o => `<tr><td>${h(o.id)}</td><td>${when(o.date)}</td><td>${o.items.reduce((n, i) => n + i.qty, 0)}</td><td>${money(o.total)}</td><td><button class="product-secondary order-details-button" data-order-details="${h(o.id)}" aria-label="Ver detalles del pedido ${h(o.id)}">Detalles</button></td></tr>`).join('') || '<tr><td colspan="5">No hay pedidos en este período. Prueba con otras fechas.</td></tr>';
    $<HTMLButtonElement>('#report-export').disabled = orders.length === 0;
  }
  function renderAdmin() {
    $('#collection-admin-list').innerHTML = commerce.collections().map(c => `<article class="collection-admin-row"><div><h3>${h(c.name)} <span class="admin-tag ${c.active ? '' : 'muted'}">${c.active ? 'Activa' : 'Inactiva'}</span></h3><p>${c.productIds.filter(id => products.some(p => p.id === id)).length} productos activos asociados · ${h(c.description)}</p></div><div class="feature-actions"><button class="product-secondary" data-collection-edit="${c.id}">Editar</button><button class="product-secondary" data-collection-toggle="${c.id}">${c.active ? 'Desactivar' : 'Reactivar'}</button></div></article>`).join('');
    const search = $<HTMLInputElement>('#stock-search').value.toLocaleLowerCase('es'); const low = $<HTMLInputElement>('#stock-low').checked;
    const stockProducts = products.filter(p => `${p.name} ${p.category}`.toLocaleLowerCase('es').includes(search) && (!low || commerce.quantity(p.id) <= 5));
    $('#stock-body').innerHTML = stockProducts.map(p => `<tr><td>${h(p.name)}</td><td>${commerce.quantity(p.id) <= 5 ? '<span class="admin-tag muted">Stock bajo</span>' : '<span class="admin-tag">Disponible</span>'}</td><td>${commerce.quantity(p.id)}</td><td><form data-stock="${p.id}" class="stock-edit"><label class="sr-only" for="stock-qty-${p.id}">Nueva cantidad de ${h(p.name)}</label><input id="stock-qty-${p.id}" name="quantity" type="number" value="${commerce.quantity(p.id)}" min="0" max="99999" step="1" required/><label class="sr-only" for="stock-reason-${p.id}">Motivo del ajuste</label><input id="stock-reason-${p.id}" name="reason" placeholder="Motivo del ajuste" minlength="3" maxlength="200" required/><button class="product-secondary">Guardar</button></form></td></tr>`).join('') || '<tr><td colspan="4">No hay productos que coincidan con los filtros.</td></tr>';
    $('#stock-history').innerHTML = commerce.changes().slice(0, 10).map(c => `<li>${h(products.find(p => p.id === c.productId)?.name ?? `Producto ${c.productId}`)}: ${c.quantity} unidades · ${h(c.reason)} · ${when(c.date)}</li>`).join('') || '<li>Aún no hay ajustes manuales.</li>';
    $('#admin-returns-body').innerHTML = commerce.returns().map(r => `<tr><td>${h(r.id)}<small>${h(r.orderId)}</small></td><td>${h(commerce.orders().find(o => o.id === r.orderId)?.items.find(p => p.productId === r.productId)?.name ?? String(r.productId))}</td><td>${h(r.reason)}<p>${h(r.comment)}</p></td><td><label class="sr-only" for="return-status-${r.id}">Estado de ${h(r.id)}</label><select id="return-status-${r.id}" data-return-status="${r.id}">${['Solicitada', 'En revisión', 'Resuelta'].map(s => `<option ${s === r.status ? 'selected' : ''}>${s}</option>`).join('')}</select></td></tr>`).join('') || '<tr><td colspan="4">No hay solicitudes de devolución por revisar.</td></tr>';
    renderReports();
  }
  function openCollection(id?: string) {
    const collection = commerce.collections().find(c => c.id === id); editingCollection = id;
    $<HTMLFormElement>('#collection-form').reset(); $('#collection-error').textContent = '';
    $('#collection-form-title').textContent = collection ? 'Editar colección' : 'Nueva colección';
    $<HTMLInputElement>('#collection-name').value = collection?.name ?? '';
    $<HTMLTextAreaElement>('#collection-description').value = collection?.description ?? '';
    $('#collection-product-options').innerHTML = products.map(p => `<label><input type="checkbox" name="product" value="${p.id}" ${collection?.productIds.includes(p.id) ? 'checked' : ''}/> ${h(p.name)}</label>`).join('') || '<p>Primero crea un producto activo.</p>';
    $('#collection-form').hidden = false; $('#collection-name').focus();
  }
  $('#collection-new').addEventListener('click', () => openCollection());
  $('#collection-cancel').addEventListener('click', () => { $('#collection-form').hidden = true; $('#collection-new').focus(); });
  $('#collection-admin-list').addEventListener('click', event => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>('button'); if (!button) return;
    if (button.dataset.collectionEdit) openCollection(button.dataset.collectionEdit);
    if (button.dataset.collectionToggle) { togglingCollection = button.dataset.collectionToggle; const c = commerce.collections().find(c => c.id === togglingCollection)!; $('#feature-confirm-text').textContent = `${c.active ? 'Desactivar' : 'Reactivar'} “${c.name}” en la tienda. Puedes revertir el cambio cuando lo necesites.`; $<HTMLDialogElement>('#feature-confirm').showModal(); $('#feature-confirm-cancel').focus(); }
  });
  $('#feature-confirm-cancel').addEventListener('click', () => $<HTMLDialogElement>('#feature-confirm').close());
  $('#feature-confirm-ok').addEventListener('click', () => { if (togglingCollection) commerce.toggleCollection(togglingCollection); $<HTMLDialogElement>('#feature-confirm').close(); changed(); notify('Estado de la colección actualizado.'); });
  $('#collection-form').addEventListener('submit', event => {
    event.preventDefault(); try { const selected = [...document.querySelectorAll<HTMLInputElement>('#collection-product-options input:checked')].map(i => Number(i.value)); const previous = commerce.collections().find(c => c.id === editingCollection); const inactiveRelations = previous?.productIds.filter(id => !products.some(p => p.id === id)) ?? []; commerce.saveCollection($<HTMLInputElement>('#collection-name').value, $<HTMLTextAreaElement>('#collection-description').value, [...selected, ...inactiveRelations], editingCollection); $('#collection-form').hidden = true; changed(); notify('Colección guardada.'); $('#collection-new').focus(); } catch (error) { $('#collection-error').textContent = error instanceof Error ? error.message : 'No pudimos guardar la colección.'; }
  });
  $('#stock-search').addEventListener('input', renderAdmin); $('#stock-low').addEventListener('change', renderAdmin);
  $('#stock-body').addEventListener('submit', event => {
    event.preventDefault(); const form = (event.target as HTMLElement).closest<HTMLFormElement>('form[data-stock]'); if (!form) return;
    try { const data = new FormData(form); commerce.setStock(Number(form.dataset.stock), Number(data.get('quantity')), String(data.get('reason'))); changed(); $('#stock-message').textContent = 'Inventario actualizado.'; } catch (error) { $('#stock-message').textContent = error instanceof Error ? error.message : 'No se pudo guardar el ajuste.'; }
  });
  for (const selector of ['#report-from', '#report-to']) $(selector).addEventListener('change', renderReports);
  $('#report-body').addEventListener('click', event => { const button = (event.target as HTMLElement).closest<HTMLButtonElement>('[data-order-details]'); if (button) orderDetails.open(button.dataset.orderDetails!, button); });
  $('#report-clear').addEventListener('click', () => { $<HTMLInputElement>('#report-from').value = ''; $<HTMLInputElement>('#report-to').value = ''; renderReports(); });
  $('#report-export').addEventListener('click', () => { const rows = [['Pedido', 'Fecha', 'Unidades', 'Total MXN'], ...selectedOrders().map(o => [o.id, o.date, String(o.items.reduce((n, p) => n + p.qty, 0)), String(o.total)])]; const url = URL.createObjectURL(new Blob(['\uFEFF' + rows.map(r => r.map(csvCell).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8' })); const a = document.createElement('a'); a.href = url; a.download = 'bagstore-ventas.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); });
  $('#admin-returns-body').addEventListener('change', event => { const select = (event.target as HTMLElement).closest<HTMLSelectElement>('[data-return-status]'); if (!select) return; try { commerce.setReturnStatus(select.dataset.returnStatus!, select.value as 'Solicitada' | 'En revisión' | 'Resuelta'); changed(); $('#admin-returns-message').textContent = 'Estado local actualizado. No se realizó un reembolso.'; } catch { $('#admin-returns-message').textContent = 'No pudimos actualizar la solicitud.'; } });
  $('#api-check').addEventListener('click', async () => {
    const env = (import.meta as ImportMeta & { env: Record<string, string | undefined> }).env;
    const button = $<HTMLButtonElement>('#api-check'); const status = $('#api-status');
    if (!env.VITE_API_BASE_URL || !env.VITE_API_HEALTH_PATH) { status.textContent = 'Conexión pendiente: faltan URL y ruta acordadas con el equipo. No se realizó ninguna petición.'; return; }
    button.disabled = true; status.textContent = 'Comprobando conexión…';
    try { await new ApiClient(env.VITE_API_BASE_URL).request(env.VITE_API_HEALTH_PATH); status.textContent = 'El endpoint configurado respondió JSON correctamente. Esto no confirma autenticación ni contratos de productos.'; }
    catch (error) { status.textContent = error instanceof Error ? error.message : 'No se pudo conectar.'; }
    finally { button.disabled = false; }
  });

  function productCards(list: Product[]) { return list.map(p => `<article class="related-product"><a href="#producto/${p.id}"><div>${visual(p, `related-${p.id}`)}</div><h3>${h(p.name)}</h3><p>${money(p.price)}</p></a></article>`).join('') || '<p>No hay productos activos asociados todavía.</p>'; }
  function detail(id: number) {
    const p = products.find(p => p.id === id);
    if (!p) return '<h1 tabindex="-1">Producto no disponible</h1><p>Puede haberse desactivado en el panel.</p><a class="button" href="#catalogo">Volver al catálogo</a>';
    const reviews = commerce.reviews(id); const average = reviews.length ? (reviews.reduce((n, r) => n + r.rating, 0) / reviews.length).toFixed(1) : null;
    return `<a class="continue-shopping" href="#catalogo">← Volver al catálogo</a><div class="detail-grid"><div class="detail-art">${visual(p, 'detail')}</div><div class="detail-copy"><p class="eyebrow">${h(p.category)} / BAGSTORE</p><h1 tabindex="-1">${h(p.name)}</h1><p class="detail-price">${money(p.price)} MXN</p><p>Color: <strong>${h(p.label)}</strong></p><p class="demo-label">${commerce.quantity(id)} unidades disponibles</p><p>Una bolsa para acompañarte en tus planes. Elige tu color favorito y llévala contigo cada día.</p><label for="detail-qty">Cantidad</label><select id="detail-qty">${Array.from({ length: Math.min(10, commerce.quantity(id)) }, (_, i) => `<option>${i + 1}</option>`).join('')}</select><div class="feature-actions"><button class="button" data-detail-add="${id}" ${commerce.quantity(id) === 0 ? 'disabled' : ''}>${commerce.quantity(id) ? 'Agregar a mi bolsa' : 'Agotado'}</button><button class="product-secondary" data-share="${id}">Compartir producto ↗</button></div><p class="demo-note">Revisa tu selección y el total antes de confirmar.</p></div></div><section class="reviews"><div class="section-heading"><h2>Lo que cuentan de esta bolsa.</h2><span>${average ? `${average} / 5 · ${reviews.length} reseñas` : 'Sin reseñas todavía'}</span></div><div class="review-list">${reviews.map(r => `<article><strong>${h(r.name)}</strong><span aria-label="${r.rating} de 5 estrellas">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span><p>${h(r.comment)}</p><small>${when(r.date)} · Opinión</small></article>`).join('') || '<p>¿Ya conoces esta bolsa? Comparte tu opinión.</p>'}</div><form id="review-form" class="feature-form" data-product="${id}"><h3>Escribe tu reseña</h3><p class="demo-note">Cuéntanos qué te gustó y qué mejorarías. Tu opinión puede ayudar a otras personas a elegir.</p><label for="review-name">Nombre visible</label><input id="review-name" name="name" required minlength="2" maxlength="40" autocomplete="off"/><label for="review-rating">Calificación</label><select id="review-rating" name="rating" required><option value="">Selecciona estrellas</option>${[5, 4, 3, 2, 1].map(n => `<option value="${n}">${n} estrellas</option>`).join('')}</select><label for="review-comment">Comentario</label><textarea id="review-comment" name="comment" required minlength="5" maxlength="1000" rows="3"></textarea><p id="review-error" class="field-error" role="alert"></p><button class="button">Publicar reseña</button></form></section>`;
  }
  function returnsPage() {
    const orders = commerce.orders();
    return `<a href="#inicio" class="continue-shopping">← Volver a la tienda</a><h1 tabindex="-1">Cambios y devoluciones.</h1><p>Selecciona tu pedido y cuéntanos qué ocurrió para registrar una solicitud.</p><div class="feature-grid"><form id="return-form" class="feature-form"><h2>Solicitar una devolución</h2><label for="return-order">Pedido</label><select id="return-order" name="order" required><option value="">Selecciona un pedido</option>${orders.map(o => `<option value="${o.id}">${h(o.id)} · ${money(o.total)}</option>`).join('')}</select><label for="return-product">Producto del pedido</label><select id="return-product" name="product" required><option value="">Primero selecciona un pedido</option></select><label for="return-reason">Motivo</label><select id="return-reason" name="reason" required><option value="">Selecciona un motivo</option><option>Producto incorrecto</option><option>Problema con el producto</option><option>Otro motivo</option></select><label for="return-comment">Cuéntanos qué pasó</label><textarea id="return-comment" name="comment" minlength="5" maxlength="1000" required rows="4"></textarea><p id="return-error" class="field-error" role="alert"></p><button class="button" ${orders.length ? '' : 'disabled'}>Enviar solicitud</button>${orders.length ? '' : '<p class="demo-note">Todavía no tienes pedidos disponibles para solicitar una devolución.</p><a href="#catalogo">Explorar catálogo →</a>'}</form><div class="feature-card"><h2>Tus solicitudes</h2>${commerce.returns().map(r => `<article class="return-card"><strong>${h(r.id)}</strong><p>${h(r.orderId)}</p><span class="admin-tag">${r.status}</span><p>${h(r.reason)}: ${h(r.comment)}</p><small>${when(r.date)}</small></article>`).join('') || '<p>Aún no hay solicitudes.</p>'}</div></div>`;
  }
  function checkoutPage(step: string) {
    const state = cart.snapshot();
    if (step === 'confirmacion' && lastOrder) return `<p class="eyebrow">CONFIRMACIÓN</p><h1 tabindex="-1">Tu pedido de vista previa está listo.</h1><div class="feature-card"><h2>${h(lastOrder.id)}</h2><p>Guardamos tu selección en esta vista previa. No se ha realizado ningún cobro ni se ha solicitado un envío.</p><p>Total: <strong>${money(lastOrder.total)}</strong></p><p>${lastOrder.delivery === 'Recoger en tienda (demo)' ? 'Recoger en tienda' : 'Envío a domicilio'} · ${lastOrder.payment === 'Tarjeta de prueba' ? 'Tarjeta' : 'Transferencia'}</p><ul>${lastOrder.items.map(i => `<li>${h(i.name)} × ${i.qty}</li>`).join('')}</ul><div class="feature-actions"><a href="#catalogo" class="button">Seguir explorando</a><a href="#devoluciones" class="product-secondary">Ver cambios y devoluciones</a></div></div>`;
    if (!state.count) return '<h1 tabindex="-1">Primero elige una favorita.</h1><p>Tu carrito está vacío o sus productos ya no están disponibles.</p><a href="#catalogo" class="button">Ver catálogo</a>';
    const paymentStep = step === 'pago';
    return `<a href="${paymentStep ? '#compra/entrega' : '#checkout'}" class="continue-shopping">← Volver al paso anterior</a><p class="eyebrow">TU COMPRA · ${paymentStep ? 'PAGO' : 'ENTREGA'}</p><h1 tabindex="-1">${paymentStep ? 'Revisa y confirma.' : '¿Cómo quieres recibir tu compra?'}</h1><div class="feature-grid"><form id="${paymentStep ? 'purchase-form' : 'delivery-form'}" class="feature-form"><h2>${paymentStep ? 'Método de pago' : 'Opciones de entrega'}</h2>${paymentStep ? `<label class="radio-option"><input type="radio" name="payment" value="Tarjeta de prueba" ${payment === 'Tarjeta de prueba' ? 'checked' : ''}/> Tarjeta · Vista previa</label><label class="radio-option"><input type="radio" name="payment" value="Transferencia de prueba" ${payment === 'Transferencia de prueba' ? 'checked' : ''}/> Transferencia · Vista previa</label><p>Los pagos aún no están habilitados. Puedes revisar este paso sin ingresar datos bancarios.</p><label class="inline-check"><input type="checkbox" name="ack" required/> Entiendo que esta confirmación es de vista previa y no genera cobros ni envíos.</label>` : `<label class="radio-option"><input type="radio" name="delivery" value="pickup" ${shipping === 0 ? 'checked' : ''}/> Recoger en tienda · $0.00</label><label class="radio-option"><input type="radio" name="delivery" value="shipping" ${shipping === 79 ? 'checked' : ''}/> Envío a domicilio · $79.00</label><label for="delivery-postcode">Código postal</label><input id="delivery-postcode" name="postcode" inputmode="numeric" pattern="[0-9]{5}" maxlength="5" placeholder="Ej. 00000" required autocomplete="off"/><p class="demo-note">Tarifas de vista previa. Por ahora no se solicita una dirección de entrega.</p>`}<p id="purchase-error" class="field-error" role="alert"></p><button class="button" id="purchase-submit">${paymentStep ? 'Confirmar vista previa' : 'Continuar al pago'}</button></form><aside class="feature-card"><h2>Tu resumen</h2><ul class="purchase-lines">${state.lines.map(line => { const p = products.find(p => p.id === line.id); return p ? `<li><span>${h(p.name)} × ${line.qty}</span><strong>${money(p.price * line.qty)}</strong></li>` : ''; }).join('')}</ul><p>Subtotal: ${money(state.subtotal)}</p><p>Descuento: −${money(state.discount)}</p><p>Envío: ${money(shipping)}</p><p class="detail-price">Total: ${money(state.total + shipping)}</p><p class="demo-note">Los importes de esta vista previa no generan cargos.</p></aside></div>`;
  }
  function route() {
    const hash = location.hash;
    if (hash.startsWith('#compra/') && !requireCustomerAccess()) { extra.hidden = true; return; }
    renderCollections(); renderAdmin();
    let markup: string | undefined;
    if (hash.startsWith('#producto/')) markup = detail(Number(hash.split('/')[1]));
    else if (hash === '#devoluciones') markup = returnsPage();
    else if (hash === '#portafolio') markup = `<p class="eyebrow">PORTAFOLIO / PRESENTACIÓN DE COLECCIONES</p><h1 tabindex="-1">El universo Bagstore.</h1><p>Explora nuestras colecciones y descubre las bolsas que acompañan cada momento.</p><div class="collection-tile-grid">${collectionsMarkup()}</div>`;
    else if (hash.startsWith('#coleccion/')) { const c = commerce.collections().find(c => c.id === hash.split('/')[1] && c.active); markup = c ? `<a href="#portafolio" class="continue-shopping">← Todas las colecciones</a><h1 tabindex="-1">${h(c.name)}</h1><p>${h(c.description)}</p><div class="related-grid">${productCards(products.filter(p => c.productIds.includes(p.id)))}</div>` : '<h1 tabindex="-1">Colección no disponible</h1><a href="#portafolio">Ver colecciones</a>'; }
    else if (hash.startsWith('#compra/')) markup = checkoutPage(hash.split('/')[1]);
    if (markup !== undefined) {
      for (const child of $('main').children) if (child instanceof HTMLElement) child.hidden = child.id !== 'extra-page';
      extra.innerHTML = markup + `<p class="demo-note storage-message" role="status">${h(commerce.warning())}</p>`;
      extra.hidden = false; document.body.classList.remove('admin-mode');
      const title = extra.querySelector<HTMLElement>('h1'); document.title = `${title?.textContent ?? 'Bagstore'} — Bagstore`; title?.focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: 'instant' });
    } else extra.hidden = true;
  }
  extra.addEventListener('click', async event => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>('button'); if (!button) return;
    if (button.dataset.detailAdd) { const qty = Number($<HTMLSelectElement>('#detail-qty').value); for (let i = 0; i < Math.min(qty, 10); i++) cart.add(Number(button.dataset.detailAdd)); }
    if (button.dataset.share) {
      const p = products.find(p => p.id === Number(button.dataset.share)); if (!p) return;
      const url = new URL(`#producto/${p.id}`, location.href).href;
      if (navigator.share) { try { await navigator.share({ title: p.name, url }); return; } catch (error) { if (error instanceof DOMException && error.name === 'AbortError') return; } }
      $<HTMLInputElement>('#share-url').value = url; $('#share-feedback').textContent = ''; $<HTMLDialogElement>('#share-dialog').showModal(); $<HTMLInputElement>('#share-url').select();
    }
  });
  $('#share-copy').addEventListener('click', async () => { try { await navigator.clipboard.writeText($<HTMLInputElement>('#share-url').value); $('#share-feedback').textContent = 'Enlace copiado.'; } catch { $<HTMLInputElement>('#share-url').select(); $('#share-feedback').textContent = 'Selecciona el enlace y usa Ctrl + C para copiarlo.'; } });
  $('#share-close').addEventListener('click', () => $<HTMLDialogElement>('#share-dialog').close());
  extra.addEventListener('change', event => {
    const select = (event.target as HTMLElement).closest<HTMLSelectElement>('#return-order'); if (!select) return;
    const order = commerce.orders().find(o => o.id === select.value);
    $<HTMLSelectElement>('#return-product').replaceChildren(new Option('Selecciona un producto', ''), ...(order?.items.map(p => new Option(p.name, String(p.productId))) ?? []));
  });
  extra.addEventListener('submit', event => {
    event.preventDefault(); const form = event.target as HTMLFormElement; const data = new FormData(form);
    if (form.id === 'review-form') { try { commerce.addReview(Number(form.dataset.product), String(data.get('name')), Number(data.get('rating')), String(data.get('comment'))); changed(); route(); notify('Reseña publicada.'); } catch (error) { $('#review-error').textContent = error instanceof Error ? error.message : 'No pudimos guardar la reseña.'; } }
    if (form.id === 'return-form') { try { commerce.requestReturn(String(data.get('order')), Number(data.get('product')), String(data.get('reason')), String(data.get('comment'))); changed(); route(); notify('Solicitud registrada. Puedes consultar su estado aquí.'); } catch (error) { $('#return-error').textContent = error instanceof Error ? error.message : 'No pudimos registrar la solicitud.'; } }
    if (form.id === 'delivery-form') { shipping = data.get('delivery') === 'shipping' ? 79 : 0; delivery = shipping ? 'Envío a domicilio (demo)' : 'Recoger en tienda (demo)'; location.hash = 'compra/pago'; }
    if (form.id === 'purchase-form' && !placingOrder) {
      if (!requireCustomerAccess()) return;
      placingOrder = true; $<HTMLButtonElement>('#purchase-submit').disabled = true;
      try { if (data.get('ack') !== 'on') throw Error('Confirma que entiendes las condiciones de esta vista previa.'); payment = String(data.get('payment')); const snapshot = cart.snapshot(); lastOrder = commerce.createOrder(snapshot.lines, products, snapshot.coupon, shipping, delivery, payment); cart.clear(); changed(); location.hash = 'compra/confirmacion'; }
      catch (error) { $('#purchase-error').textContent = error instanceof Error ? error.message : 'No pudimos guardar tu selección. Inténtalo de nuevo.'; $<HTMLButtonElement>('#purchase-submit').disabled = false; }
      finally { placingOrder = false; }
    }
  });
  window.addEventListener('hashchange', route);
  window.addEventListener('bagstore-products-changed', () => { renderCollections(); renderAdmin(); if (location.hash.startsWith('#producto/')) route(); });
  route();
}
