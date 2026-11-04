import type { CommerceRepository, DemoOrder } from '../services/commerce';
import { escapeHtml as h, money } from '../ui';
import '../order-details.css';

interface ShipmentReference { carrier: string; tracking: string; }
const KEY = 'bagstore.shipment-references.v1';

export function setupOrderDetails(commerce: CommerceRepository) {
  const dialog = document.createElement('dialog');
  dialog.id = 'order-detail'; dialog.className = 'order-detail';
  dialog.setAttribute('aria-labelledby', 'order-detail-title');
  document.body.append(dialog);
  let selected: DemoOrder | undefined;
  let opener: HTMLElement | null = null;
  let references: Record<string, ShipmentReference> = {};
  let warning = '';
  try {
    const data = JSON.parse(localStorage.getItem(KEY) ?? '{}');
    if (!data || Array.isArray(data) || typeof data !== 'object') throw Error();
    for (const [id, ref] of Object.entries(data)) {
      const r = ref as ShipmentReference;
      if (!/^[a-z0-9-]+$/i.test(id) || !r || typeof r.carrier !== 'string' || typeof r.tracking !== 'string' || r.carrier.length > 80 || r.tracking.length > 100) throw Error();
    }
    references = data;
  } catch { warning = 'No pudimos recuperar las referencias de envío guardadas. Revisa la guía antes de preparar el paquete.'; }
  function render() {
    if (!selected) return;
    const order = selected;
    const ref = references[order.id];
    const pickup = order.delivery === 'Recoger en tienda (demo)';
    dialog.innerHTML = `<div class="ticket-toolbar"><h2 id="order-detail-title">Detalles del pedido</h2><button type="button" id="order-detail-close" class="product-secondary">Cerrar</button></div>
      <article class="order-ticket" aria-label="Ticket de preparación del pedido">
        <header class="ticket-header"><strong>bagstore</strong><span>TICKET DE PREPARACIÓN</span><h3>${h(order.id)}</h3><p>${h(new Date(order.date).toLocaleString('es-MX'))}</p></header>
        <div class="ticket-meta"><p><strong>Entrega</strong><br/>${pickup ? 'Recoger en tienda' : 'Envío a domicilio'}</p><p><strong>Método de pago seleccionado</strong><br/>${order.payment === 'Tarjeta de prueba' ? 'Tarjeta' : order.payment === 'Transferencia de prueba' ? 'Transferencia' : h(order.payment)}</p></div>
        <p class="ticket-note">Vista previa · Sin comprobación de pago. Este documento no es una factura ni una etiqueta de paquetería.</p>
        <h4>Productos para preparar</h4><div class="ticket-table-scroll"><table><thead><tr><th scope="col">Referencia / producto</th><th scope="col">Cantidad</th><th scope="col">Precio</th><th scope="col">Importe</th><th scope="col">Preparado</th></tr></thead><tbody>${order.items.map(i => `<tr><td><small>BS-${String(i.productId).padStart(3, '0')}</small><br/>${h(i.name)}<br/><small>Color: ${h(i.color || 'No registrado en este pedido')}</small></td><td>${i.qty}</td><td>${money(i.price)}</td><td>${money(i.price * i.qty)}</td><td><span class="ticket-check" aria-label="Casilla para marcar al preparar">□</span></td></tr>`).join('')}</tbody></table></div>
        <dl class="ticket-totals"><div><dt>Subtotal</dt><dd>${money(order.subtotal)}</dd></div><div><dt>Descuento</dt><dd>−${money(order.discount)}</dd></div><div><dt>Envío</dt><dd>${money(order.shipping)}</dd></div><div><dt>Total MXN</dt><dd>${money(order.total)}</dd></div><div><dt>Unidades a preparar</dt><dd>${order.items.reduce((n, i) => n + i.qty, 0)}</dd></div></dl>
        <section class="ticket-shipment"><h4>Referencia de envío</h4><p><strong>Paquetería:</strong> ${h(ref?.carrier || 'Sin asignar')}</p><p><strong>Número de guía:</strong> ${h(ref?.tracking || (pickup ? 'No aplica: recoger en tienda' : 'Sin asignar'))}</p><p><strong>Destinatario y dirección:</strong> no disponibles en los pedidos locales actuales.</p></section>
        <div class="ticket-signoff"><span>Preparó: __________________</span><span>Revisó: __________________</span></div>
      </article>
      ${pickup ? '' : `<form id="order-shipment-form" class="feature-form ticket-no-print"><h3>Vincular una guía existente</h3><p>Registra la guía emitida por tu paquetería para identificar qué productos lleva este paquete. Se guarda solo en este navegador; no genera una guía ni contrata un envío.</p><label for="order-carrier">Paquetería</label><input id="order-carrier" name="carrier" maxlength="80" value="${h(ref?.carrier ?? '')}" required/><label for="order-tracking">Número de guía</label><input id="order-tracking" name="tracking" maxlength="100" value="${h(ref?.tracking ?? '')}" required/><button class="product-secondary">Guardar referencia</button></form>`}
      <p id="order-detail-message" class="ticket-no-print" role="status">${h(warning)}</p><div class="feature-actions ticket-no-print"><button id="order-ticket-print" class="button" type="button">Imprimir ticket</button><p>En la ventana de impresión también puedes elegir Guardar como PDF.</p></div>`;
  }
  dialog.addEventListener('submit', event => {
    event.preventDefault(); if (!selected) return;
    const form = event.target as HTMLFormElement; if (form.id !== 'order-shipment-form' || !form.reportValidity()) return;
    const data = new FormData(form); const carrier = String(data.get('carrier') ?? '').trim(); const tracking = String(data.get('tracking') ?? '').trim();
    const message = dialog.querySelector<HTMLElement>('#order-detail-message')!;
    if (!carrier || !tracking || carrier.length > 80 || tracking.length > 100) { message.textContent = 'Escribe la paquetería y el número de guía.'; return; }
    const next = { ...references, [selected.id]: { carrier, tracking } };
    try { localStorage.setItem(KEY, JSON.stringify(next)); references = next; warning = ''; render(); dialog.querySelector<HTMLElement>('#order-detail-message')!.textContent = 'Referencia de envío guardada para este pedido.'; dialog.querySelector<HTMLElement>('#order-tracking')?.focus(); }
    catch { message.textContent = 'No pudimos guardar la referencia. Revisa el almacenamiento del navegador e inténtalo de nuevo.'; }
  });
  dialog.addEventListener('click', event => {
    const id = (event.target as HTMLElement).closest('button')?.id;
    if (id === 'order-detail-close') dialog.close();
    if (id === 'order-ticket-print') {
      document.body.classList.add('printing-order');
      try { window.print(); } catch { document.body.classList.remove('printing-order'); dialog.querySelector<HTMLElement>('#order-detail-message')!.textContent = 'No pudimos abrir la impresión. Inténtalo desde el navegador.'; }
    }
  });
  window.addEventListener('afterprint', () => document.body.classList.remove('printing-order'));
  dialog.addEventListener('close', () => { document.body.classList.remove('printing-order'); selected = undefined; if (opener?.isConnected) opener.focus(); });
  window.addEventListener('hashchange', () => { if (dialog.open) dialog.close(); });
  return { open(id: string, button: HTMLElement) { const order = commerce.orders().find(o => o.id === id); if (!order) return; selected = order; opener = button; render(); dialog.showModal(); dialog.querySelector<HTMLElement>('#order-detail-close')?.focus(); } };
}
