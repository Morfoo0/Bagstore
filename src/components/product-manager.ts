import { products } from '../data/products';
import { requestedTestProduct, testProductRequestKey } from '../data/admin-test-product';
import { bagArt } from './bag';
import { prepareProductPhoto } from '../services/product-photo';
import { createProductRepository, validateProduct } from '../services/admin-products';
import type { ProductDraft } from '../services/admin-products';
import type { AdminProduct } from '../services/admin-products';
import { baseCategories, legacyColorId, normalizedName } from '../services/catalogs';
import type { CatalogRepository } from '../services/catalogs';

const fields = ['name', 'category', 'label', 'color', 'accent', 'price'] as const;
function get<T extends HTMLElement = HTMLElement>(selector: string): T {
  const result = document.querySelector<T>(selector);
  if (!result) throw new Error(`Elemento de productos no encontrado: ${selector}`);
  return result;
}
function safe(value: string): string {
  return value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]!);
}

export function setupProductManager(catalogs: CatalogRepository): void {
  let storage: Storage | undefined;
  try { storage = localStorage; } catch { /* El repositorio informará si no puede persistir. */ }
  const repo = createProductRepository(products, storage, () => catalogs.categories().map(c => c.name));
  const categoryFor = (p: AdminProduct) => catalogs.categories().find(c => c.id === p.categoryId) ?? catalogs.categories().find(c => normalizedName(c.name) === normalizedName(p.category)) ?? catalogs.categories().find(c => c.id === baseCategories.find(v => normalizedName(v.name) === normalizedName(p.category))?.id);
  const colorFor = (p: AdminProduct) => catalogs.colors().find(c => c.id === p.colorId) ?? catalogs.colors().find(c => c.id === legacyColorId(p.label)) ?? catalogs.colors().find(c => normalizedName(c.name) === normalizedName(p.label));
  function publishProducts() {
    products.splice(0, products.length, ...repo.list().filter(p => p.active).map(p => ({ ...p, category: categoryFor(p)?.name ?? p.category, categoryId: categoryFor(p)?.id, label: colorFor(p)?.name ?? p.label, colorId: colorFor(p)?.id })));
    window.dispatchEvent(new Event('bagstore-products-changed'));
  }
  // Aplicar una vez la solicitud de prueba al abrir/recargar el panel.
  // La marca evita recrearlo si después el usuario cambia su nombre o estado.
  try {
    if (!storage?.getItem(testProductRequestKey)) {
      if (!repo.list().some(p => p.name === requestedTestProduct.name)) repo.save(requestedTestProduct);
      storage?.setItem(testProductRequestKey, 'created');
    }
  } catch {
    // Si el navegador bloquea la persistencia, el repositorio conserva el aviso.
  }
  // Conservar opciones de productos antiguos sin convertirlas en duplicados.
  for (const p of repo.list()) {
    if (!categoryFor(p)) try { catalogs.addCategory(p.category); } catch { /* Se mostrará sin selección si no es válida. */ }
    if (!colorFor(p)) try { catalogs.addColor(p.label, p.color); } catch { /* Mantener el producto original. */ }
  }
  repo.bindCatalogs(p => ({ categoryId: categoryFor(p)?.id, colorId: colorFor(p)?.id }));
  const dialog = get<HTMLDialogElement>('#product-editor');
  const confirmation = get<HTMLDialogElement>('#product-confirm');
  const form = get<HTMLFormElement>('#product-editor-form');
  let editing: number | undefined;
  let changing: number | undefined;
  let opener: HTMLElement | null = null;
  let dirty = false;
  let photo: string | undefined;
  let photoName: string | undefined;
  let photoVersion = 0;
  let photoBusy = false;
  let catalogKind: 'color' | 'category' = 'color';
  let categoryEditing: string | undefined;
  let catalogOpener: HTMLElement | null = null;
  const catalogDialog = get<HTMLDialogElement>('#catalog-editor');

  function refreshSelectors() {
    for (const [selector, values, placeholder] of [
      ['#product-category', catalogs.categories(), 'Selecciona una categoría'],
      ['#product-label', catalogs.colors(), 'Selecciona un color'],
      ['#admin-color-filter', catalogs.colors(), 'Todos los colores']
    ] as const) {
      const select = get<HTMLSelectElement>(selector);
      const previous = select.value;
      select.replaceChildren(new Option(placeholder, ''), ...values.map(c => new Option(c.name, c.id)));
      if (values.some(c => c.id === previous)) select.value = previous;
    }
  }
  function renderCategories() {
    const list = catalogs.categories();
    get('#admin-category-count').textContent = String(list.length);
    get('#admin-categories').innerHTML = list.map(c => `<article class="admin-category"><span aria-hidden="true">◇</span><h3>${safe(c.name)}</h3><p>${repo.list().filter(p => categoryFor(p)?.id === c.id).length} productos del panel</p><button class="product-secondary" data-category-edit="${c.id}" aria-label="Renombrar ${safe(c.name)}">Renombrar</button></article>`).join('');
    get('#catalog-storage-warning').textContent = catalogs.warning();
    get('#catalog-storage-warning').hidden = !catalogs.warning();
  }
  function openCatalog(kind: 'color' | 'category', id?: string) {
    catalogKind = kind; categoryEditing = id; catalogOpener = document.activeElement as HTMLElement;
    get<HTMLFormElement>('#catalog-form').reset();
    get('#catalog-error').hidden = true;
    get('#catalog-tone-field').hidden = kind !== 'color';
    get('#catalog-editor-title').textContent = kind === 'color' ? 'Agregar un color' : id ? 'Renombrar categoría' : 'Nueva categoría';
    get('#catalog-name-label').textContent = kind === 'color' ? 'Nombre del color' : 'Nombre de la categoría';
    if (id) get<HTMLInputElement>('#catalog-name').value = catalogs.categories().find(c => c.id === id)?.name ?? '';
    catalogDialog.showModal(); get('#catalog-name').focus();
  }
  get('#product-add-color').addEventListener('click', () => openCatalog('color'));
  get('#category-new').addEventListener('click', () => openCatalog('category'));
  get('#admin-categories').addEventListener('click', event => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>('[data-category-edit]');
    if (button) openCatalog('category', button.dataset.categoryEdit);
  });
  get('#catalog-cancel').addEventListener('click', () => catalogDialog.close());
  catalogDialog.addEventListener('close', () => { if (catalogOpener?.isConnected) catalogOpener.focus(); });
  get('#catalog-form').addEventListener('submit', event => {
    event.preventDefault();
    try {
      const name = get<HTMLInputElement>('#catalog-name').value;
      const option = catalogKind === 'color' ? catalogs.addColor(name, get<HTMLInputElement>('#catalog-tone').value) : categoryEditing ? catalogs.renameCategory(categoryEditing, name) : catalogs.addCategory(name);
      refreshSelectors();
      if (catalogKind === 'color' && dialog.open) { get<HTMLSelectElement>('#product-label').value = option.id; dirty = true; preview(); }
      catalogDialog.close(); render(); publishProducts();
      if (catalogKind === 'category') document.querySelector<HTMLButtonElement>(`[data-category-edit="${option.id}"]`)?.focus();
      get('#category-status').textContent = catalogKind === 'category' ? `Categoría ${option.name} guardada.` : '';
      window.dispatchEvent(new Event('bagstore-catalogs-changed'));
    } catch (error) {
      get('#catalog-error').textContent = error instanceof Error ? error.message : 'No pudimos guardar la opción.';
      get('#catalog-error').hidden = false; get('#catalog-name').focus();
    }
  });

  function setPhotoBusy(busy: boolean) {
    photoBusy = busy;
    get<HTMLButtonElement>('#product-save').disabled = busy;
    get('#product-photo-status').textContent = busy ? 'Preparando foto…' : '';
  }

  function announce(message: string) { get('#product-status').textContent = message; }
  function render() {
    const all = repo.list();
    const query = get<HTMLInputElement>('#admin-product-search').value.trim().toLocaleLowerCase('es');
    const state = get<HTMLSelectElement>('#admin-product-state').value;
    const colorId = get<HTMLSelectElement>('#admin-color-filter').value;
    const visible = all.filter(p => `${p.name} ${colorFor(p)?.name ?? p.label} BS-${String(p.id).padStart(3, '0')}`.toLocaleLowerCase('es').includes(query) && (state === 'all' || p.active === (state === 'active')) && (!colorId || colorFor(p)?.id === colorId));
    get('#admin-product-count').textContent = String(all.length);
    get('#product-result-count').textContent = `${visible.length} de ${all.length} productos · ${all.filter(p => p.active).length} activos`;
    get('#admin-product-rows').innerHTML = visible.map(p => `<tr><td><div class="admin-product-name"><span>${p.imageData ? `<img class="product-table-photo" src="${p.imageData}" alt="Foto de ${safe(p.name)}"/>` : bagArt(p, 'managed')}</span><div><strong>${safe(p.name)}</strong><small>BS-${String(p.id).padStart(3, '0')}</small></div></div></td><td>${safe(categoryFor(p)?.name ?? p.category)}</td><td>${safe(colorFor(p)?.name ?? p.label)}</td><td>${new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(p.price)}</td><td><span class="admin-tag ${p.active ? '' : 'muted'}">${p.active ? 'Activo' : 'Inactivo'}</span></td><td><div class="product-row-actions"><button data-edit="${p.id}" aria-label="Editar ${safe(p.name)}">Editar</button><button data-active="${p.id}" aria-label="${p.active ? 'Desactivar' : 'Reactivar'} ${safe(p.name)}">${p.active ? 'Desactivar' : 'Reactivar'}</button></div></td></tr>`).join('');
    get('#product-list-empty').hidden = visible.length > 0;
    get('#product-storage-warning').textContent = [repo.warning(), catalogs.warning()].filter(Boolean).join(' ');
    get('#product-storage-warning').hidden = !repo.warning() && !catalogs.warning();
    renderCategories();
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
    photoVersion++;
    photo = product?.imageData; photoName = product?.imageName;
    setPhotoBusy(false);
    get('#product-photo-error').textContent = '';
    form.reset(); clearErrors();
    get('#product-editor-title').textContent = product ? 'Editar producto' : 'Una nueva favorita.';
    get('#product-save').textContent = product ? 'Guardar cambios' : 'Crear producto';
    refreshSelectors();
    if (product) {
      for (const key of fields) if (key !== 'category' && key !== 'label') get<HTMLInputElement | HTMLSelectElement>(`#product-${key}`).value = String(product[key]);
      get<HTMLSelectElement>('#product-category').value = categoryFor(product)?.id ?? '';
      get<HTMLSelectElement>('#product-label').value = colorFor(product)?.id ?? '';
    }
    preview(); dialog.showModal(); get('#product-name').focus();
  }
  function preview() {
    const color = get<HTMLInputElement>('#product-color').value;
    const accent = get<HTMLInputElement>('#product-accent').value;
    const category = catalogs.categories().find(c => c.id === get<HTMLSelectElement>('#product-category').value)?.name;
    get('#product-art-preview').innerHTML = photo ? `<img src="${photo}" alt="Vista previa de la foto del producto"/>` : bagArt({ id: 0, category: category === 'Mini' || category === 'Crossbody' ? category : 'Tote', color, accent }, 'editor');
    get('#product-photo-thumb').innerHTML = photo ? `<img src="${photo}" alt="Foto seleccionada para el producto"/>` : '<span aria-hidden="true">＋</span>';
    get('#product-photo-name').textContent = photoName ?? 'Sin foto seleccionada. Se mostrará una ilustración.';
    get('#product-preview-description').textContent = photo ? 'Foto del producto seleccionada.' : 'Añade una foto para mostrar mejor tu producto.';
    get('#product-photo-remove').hidden = !photo;
    get('#product-preview-name').textContent = get<HTMLInputElement>('#product-name').value.trim() || 'Tu próxima favorita';
    const selected = catalogs.colors().find(c => c.id === get<HTMLSelectElement>('#product-label').value);
    get('#product-color-swatch').style.background = selected?.tone ?? 'transparent';
    get('#product-color-description').textContent = selected ? `Color para filtros: ${selected.name}` : 'Selecciona el color que usarán los filtros.';
  }
  function requestClose() {
    if (!dirty) { dialog.close(); return; }
    get('#product-discard').hidden = false;
    get('#product-discard-stay').focus();
  }
  get('#product-new').addEventListener('click', () => open());
  get('#admin-product-search').addEventListener('input', render);
  get('#admin-product-state').addEventListener('change', render);
  get('#admin-color-filter').addEventListener('change', render);
  get('#product-filters-clear').addEventListener('click', () => {
    get<HTMLInputElement>('#admin-product-search').value = '';
    get<HTMLSelectElement>('#admin-product-state').value = 'all'; render(); get('#admin-product-search').focus();
    get<HTMLSelectElement>('#admin-color-filter').value = ''; render();
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
      get('#product-confirm-action').textContent = product.active ? 'Desactivar producto' : 'Reactivar producto';
      get('#product-confirm-error').hidden = true;
      confirmation.showModal(); get('#product-confirm-cancel').focus();
    }
  });
  form.addEventListener('input', () => { dirty = true; preview(); });
  get('#product-photo').addEventListener('change', async () => {
    const input = get<HTMLInputElement>('#product-photo');
    const file = input.files?.[0];
    if (!file) return;
    const version = ++photoVersion;
    dirty = true; setPhotoBusy(true);
    get('#product-photo-error').textContent = '';
    try {
      const prepared = await prepareProductPhoto(file);
      if (version !== photoVersion || !dialog.open) return;
      photo = prepared.data; photoName = prepared.name; preview();
    } catch (error) {
      if (version !== photoVersion) return;
      get('#product-photo-error').textContent = `${error instanceof Error ? error.message : 'No pudimos cargar la foto.'} La selección anterior se conserva.`;
    } finally {
      if (version === photoVersion) { input.value = ''; setPhotoBusy(false); }
    }
  });
  get('#product-photo-remove').addEventListener('click', () => {
    photoVersion++; setPhotoBusy(false); photo = undefined; photoName = undefined; dirty = true;
    get<HTMLInputElement>('#product-photo').value = '';
    get('#product-photo-error').textContent = ''; preview(); get('#product-photo').focus();
  });
  form.addEventListener('submit', event => {
    event.preventDefault(); clearErrors();
    if (photoBusy) return;
    const draft = Object.fromEntries(fields.map(key => [key, get<HTMLInputElement | HTMLSelectElement>(`#product-${key}`).value])) as unknown as ProductDraft;
    const selectedCategory = catalogs.categories().find(c => c.id === draft.category);
    const selectedColor = catalogs.colors().find(c => c.id === draft.label);
    draft.category = selectedCategory?.name ?? ''; draft.categoryId = selectedCategory?.id;
    draft.label = selectedColor?.name ?? ''; draft.colorId = selectedColor?.id;
    draft.imageData = photo; draft.imageName = photoName;
    const errors = validateProduct(draft, catalogs.categories().map(c => c.name));
    if (!selectedColor) errors.label = 'Selecciona un color de la lista.';
    if (errors.imageData || errors.imageName) {
      get('#product-photo-error').textContent = errors.imageData ?? errors.imageName!;
      get('#product-photo').focus(); return;
    }
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
      dirty = false; dialog.close(); render(); publishProducts(); announce(`${saved.name}: ${updated ? 'cambios guardados' : 'producto creado'} en el catálogo.`);
      (document.querySelector<HTMLButtonElement>(`[data-edit="${saved.id}"]`) ?? get('#product-new')).focus();
    } catch (error) {
      get('#product-form-error').textContent = error instanceof Error ? error.message : 'No pudimos guardar el producto.';
      get('#product-form-error').hidden = false; get('#product-form-error').focus();
    }
  });
  dialog.addEventListener('cancel', event => { event.preventDefault(); requestClose(); });
  dialog.addEventListener('close', () => { photoVersion++; setPhotoBusy(false); get('#product-discard').hidden = true; if (opener?.isConnected) opener.focus(); });
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
      repo.setActive(product.id, !product.active); confirmation.close(); render(); publishProducts();
      announce(`${product.name}: ${product.active ? 'desactivado' : 'reactivado'}. Sus datos se conservaron.`);
      (document.querySelector<HTMLButtonElement>(`[data-active="${product.id}"]`) ?? get('#product-new')).focus();
    } catch { get('#product-confirm-error').hidden = false; }
  });
  refreshSelectors(); render(); publishProducts();
}
