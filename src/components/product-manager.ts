import { products } from '../data/products';
import { bagArt } from './bag';
import { createProductRepository, validateProduct } from '../services/admin-products';
import type { ProductDraft } from '../services/admin-products';

const fields = ['name', 'category', 'label', 'color', 'accent', 'price'] as const;
function get<T extends HTMLElement = HTMLElement>(selector: string): T {
  const result = document.querySelector<T>(selector);
  if (!result) throw new Error(`Elemento de productos no encontrado: ${selector}`);
  return result;
}
function safe(value: string): string {
  return value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]!);
}

export function setupProductManager(): void {
  let storage: Storage | undefined;
  try { storage = localStorage; } catch { /* El repositorio informará si no puede persistir. */ }
  const repo = createProductRepository(products, storage);
  const dialog = get<HTMLDialogElement>('#product-editor');
  const confirmation = get<HTMLDialogElement>('#product-confirm');
  const form = get<HTMLFormElement>('#product-editor-form');
  let editing: number | undefined;
  let changing: number | undefined;
  let opener: HTMLElement | null = null;
  let dirty = false;

  function announce(message: string) { get('#product-status').textContent = message; }
  function render() {
    const all = repo.list();
    const query = get<HTMLInputElement>('#admin-product-search').value.trim().toLocaleLowerCase('es');
    const state = get<HTMLSelectElement>('#admin-product-state').value;
    const visible = all.filter(p => `${p.name} ${p.label} BS-${String(p.id).padStart(3, '0')}`.toLocaleLowerCase('es').includes(query) && (state === 'all' || p.active === (state === 'active')));
    get('#admin-product-count').textContent = String(all.length);
    get('#product-result-count').textContent = `${visible.length} de ${all.length} productos · ${all.filter(p => p.active).length} activos`;
    get('#admin-product-rows').innerHTML = visible.map(p => `<tr><td><div class="admin-product-name"><span>${bagArt(p, 'managed')}</span><div><strong>${safe(p.name)}</strong><small>BS-${String(p.id).padStart(3, '0')}</small></div></div></td><td>${p.category}</td><td>${safe(p.label)}</td><td>${new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(p.price)}</td><td><span class="admin-tag ${p.active ? '' : 'muted'}">${p.active ? 'Activo' : 'Inactivo'}</span></td><td><div class="product-row-actions"><button data-edit="${p.id}" aria-label="Editar ${safe(p.name)}">Editar</button><button data-active="${p.id}" aria-label="${p.active ? 'Desactivar' : 'Reactivar'} ${safe(p.name)}">${p.active ? 'Desactivar' : 'Reactivar'}</button></div></td></tr>`).join('');
    get('#product-list-empty').hidden = visible.length > 0;
    get('#product-storage-warning').textContent = repo.warning();
    get('#product-storage-warning').hidden = !repo.warning();
  }
  function clearErrors() {
    get('#product-form-error').hidden = true;
    for (const key of fields) {
      get(`#product-${key}`).removeAttribute('aria-invalid');
      get(`#product-${key}-error`).textContent = '';
    }
  }
  function open(id?: number) {
    const product = repo.list().find(p => p.id === id);
    if (id !== undefined && !product) return;
    opener = document.activeElement as HTMLElement;
    editing = id; dirty = false;
    form.reset(); clearErrors();
    get('#product-editor-title').textContent = product ? 'Editar producto' : 'Una nueva favorita.';
    get('#product-save').textContent = product ? 'Guardar cambios de prueba' : 'Crear producto de prueba';
    if (product) for (const key of fields) get<HTMLInputElement | HTMLSelectElement>(`#product-${key}`).value = String(product[key]);
    preview(); dialog.showModal(); get('#product-name').focus();
  }
  function preview() {
    const color = get<HTMLInputElement>('#product-color').value;
    const accent = get<HTMLInputElement>('#product-accent').value;
    const category = get<HTMLSelectElement>('#product-category').value;
    get('#product-art-preview').innerHTML = bagArt({ id: 0, category: category === 'Mini' || category === 'Crossbody' ? category : 'Tote', color, accent }, 'editor');
    get('#product-preview-name').textContent = get<HTMLInputElement>('#product-name').value.trim() || 'Tu próxima favorita';
  }
  function requestClose() {
    if (!dirty) { dialog.close(); return; }
    get('#product-discard').hidden = false;
    get('#product-discard-stay').focus();
  }
  get('#product-new').addEventListener('click', () => open());
  get('#admin-product-search').addEventListener('input', render);
  get('#admin-product-state').addEventListener('change', render);
  get('#product-filters-clear').addEventListener('click', () => {
    get<HTMLInputElement>('#admin-product-search').value = '';
    get<HTMLSelectElement>('#admin-product-state').value = 'all'; render(); get('#admin-product-search').focus();
  });
  get('#admin-product-rows').addEventListener('click', event => {
    const target = (event.target as HTMLElement).closest<HTMLButtonElement>('button');
    if (!target) return;
    if (target.dataset.edit) open(Number(target.dataset.edit));
    if (target.dataset.active) {
      changing = Number(target.dataset.active);
      const product = repo.list().find(p => p.id === changing);
      if (!product) return;
      opener = target;
      get('#product-confirm-title').textContent = product.active ? '¿Desactivar este producto?' : '¿Reactivar este producto?';
      get('#product-confirm-name').textContent = product.name;
      get('#product-confirm-action').textContent = product.active ? 'Sí, desactivar de prueba' : 'Sí, reactivar de prueba';
      get('#product-confirm-error').hidden = true;
      confirmation.showModal(); get('#product-confirm-cancel').focus();
    }
  });
  form.addEventListener('input', () => { dirty = true; preview(); });
  form.addEventListener('submit', event => {
    event.preventDefault(); clearErrors();
    const draft = Object.fromEntries(fields.map(key => [key, get<HTMLInputElement | HTMLSelectElement>(`#product-${key}`).value])) as unknown as ProductDraft;
    const errors = validateProduct(draft);
    const invalid = fields.filter(key => errors[key]);
    if (invalid.length) {
      for (const key of invalid) { get(`#product-${key}`).setAttribute('aria-invalid', 'true'); get(`#product-${key}-error`).textContent = errors[key]!; }
      get('#product-form-error').textContent = 'Revisa los campos señalados antes de guardar.';
      get('#product-form-error').hidden = false;
      get(`#product-${invalid[0]}`).focus(); return;
    }
    try {
      const saved = repo.save(draft, editing);
      const updated = editing !== undefined;
      dirty = false; dialog.close(); render(); announce(`${saved.name}: ${updated ? 'cambios guardados' : 'producto creado'} en la demostración del panel.`);
      (document.querySelector<HTMLButtonElement>(`[data-edit="${saved.id}"]`) ?? get('#product-new')).focus();
    } catch (error) {
      get('#product-form-error').textContent = error instanceof Error ? error.message : 'No pudimos guardar el producto.';
      get('#product-form-error').hidden = false; get('#product-form-error').focus();
    }
  });
  dialog.addEventListener('cancel', event => { event.preventDefault(); requestClose(); });
  dialog.addEventListener('close', () => { get('#product-discard').hidden = true; if (opener?.isConnected) opener.focus(); });
  get('#product-editor-close').addEventListener('click', requestClose);
  get('#product-editor-cancel').addEventListener('click', requestClose);
  get('#product-discard-stay').addEventListener('click', () => { get('#product-discard').hidden = true; get('#product-name').focus(); });
  get('#product-discard-confirm').addEventListener('click', () => { dirty = false; dialog.close(); });
  get('#product-confirm-cancel').addEventListener('click', () => confirmation.close());
  confirmation.addEventListener('close', () => { if (opener?.isConnected) opener.focus(); });
  get('#product-confirm-action').addEventListener('click', () => {
    const product = repo.list().find(p => p.id === changing);
    if (!product) return;
    try {
      repo.setActive(product.id, !product.active); confirmation.close(); render();
      announce(`${product.name}: ${product.active ? 'desactivado' : 'reactivado'} en la demostración. No se borraron sus datos.`);
      (document.querySelector<HTMLButtonElement>(`[data-active="${product.id}"]`) ?? get('#product-new')).focus();
    } catch { get('#product-confirm-error').hidden = false; }
  });
  render();
}
