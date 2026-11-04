import type { Product } from '../types/product';

export interface AdminProduct extends Product { active: boolean; }
export interface ProductDraft { name: string; category: string; label: string; color: string; accent: string; price: string; }
export type DraftErrors = Partial<Record<keyof ProductDraft, string>>;
export interface DemoStorage { getItem(key: string): string | null; setItem(key: string, value: string): void; }
export const ADMIN_STORAGE_KEY = 'bagstore.admin-products.v1';
const categories = ['Tote', 'Crossbody', 'Mini'];
const hex = /^#[0-9a-f]{6}$/i;

export function validateProduct(draft: ProductDraft): DraftErrors {
  const errors: DraftErrors = {};
  if (draft.name.trim().length < 3 || draft.name.trim().length > 80) errors.name = 'Escribe un nombre de 3 a 80 caracteres.';
  if (!categories.includes(draft.category)) errors.category = 'Selecciona una categoría de la lista.';
  if (draft.label.trim().length < 2 || draft.label.trim().length > 40) errors.label = 'Escribe un nombre de color de 2 a 40 caracteres.';
  if (!hex.test(draft.color)) errors.color = 'Usa un tono hexadecimal válido, por ejemplo #CDB89E.';
  if (!hex.test(draft.accent)) errors.accent = 'Usa un tono hexadecimal válido para el detalle.';
  const price = Number(draft.price);
  if (!/^\d+(\.\d{1,2})?$/.test(draft.price) || !Number.isFinite(price) || price <= 0 || price > 999999.99) errors.price = 'Ingresa un precio mayor que 0, con máximo 2 decimales y hasta $999,999.99.';
  return errors;
}

function validSavedProduct(value: unknown): value is AdminProduct {
  if (!value || typeof value !== 'object') return false;
  const p = value as Record<string, unknown>;
  if (!Number.isSafeInteger(p.id) || Number(p.id) <= 0 || typeof p.active !== 'boolean' || typeof p.price !== 'number') return false;
  for (const key of ['name', 'category', 'label', 'color', 'accent']) if (typeof p[key] !== 'string') return false;
  return Object.keys(validateProduct({ name: p.name as string, category: p.category as string, label: p.label as string, color: p.color as string, accent: p.accent as string, price: String(p.price) })).length === 0;
}

/** Repositorio exclusivo de la demostración administrativa. No representa una API. */
export function createProductRepository(seed: Product[], storage?: DemoStorage) {
  let items: AdminProduct[] = seed.map(p => ({ ...p, active: true }));
  let storageWarning = '';
  try {
    const raw = storage?.getItem(ADMIN_STORAGE_KEY);
    if (raw) {
      const parsed: unknown = JSON.parse(raw);
      if (!Array.isArray(parsed) || !parsed.every(validSavedProduct) || new Set(parsed.map(p => p.id)).size !== parsed.length) throw new Error('Datos incompatibles');
      items = parsed.map(p => ({ ...p }));
    }
  } catch { storageWarning = 'No pudimos recuperar los datos guardados. Se cargaron los ejemplos iniciales.'; }

  function persist() {
    try {
      if (!storage) throw new Error('Sin almacenamiento');
      storage.setItem(ADMIN_STORAGE_KEY, JSON.stringify(items));
      storageWarning = '';
    } catch { storageWarning = 'No se pudo guardar en este navegador. Los cambios solo permanecerán mientras la página siga abierta.'; }
  }
  return {
    list: () => items.map(p => ({ ...p })),
    warning: () => storageWarning,
    save(draft: ProductDraft, id?: number): AdminProduct {
      if (Object.keys(validateProduct(draft)).length) throw new Error('Revisa los campos del producto.');
      const index = id === undefined ? -1 : items.findIndex(p => p.id === id);
      if (id !== undefined && index === -1) throw new Error('El producto ya no está disponible en la demostración.');
      const product: AdminProduct = {
        id: id ?? Math.max(0, ...items.map(p => p.id)) + 1,
        active: index >= 0 ? items[index].active : true,
        name: draft.name.trim(), category: draft.category as Product['category'], label: draft.label.trim(),
        color: draft.color, accent: draft.accent, price: Number(draft.price)
      };
      if (index >= 0) items[index] = product; else items.push(product);
      persist(); return { ...product };
    },
    setActive(id: number, active: boolean) {
      const product = items.find(p => p.id === id);
      if (!product) throw new Error('Producto no encontrado.');
      product.active = active; persist();
    }
  };
}
