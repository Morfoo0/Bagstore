import type { Product } from '../types/product';

export interface AdminProduct extends Product { active: boolean; imageData?: string; imageName?: string; }
export interface ProductDraft { name: string; category: string; categoryId?: string; colorId?: string; label: string; color: string; accent: string; price: string; imageData?: string; imageName?: string; }
export type DraftErrors = Partial<Record<keyof ProductDraft, string>>;
export interface DemoStorage { getItem(key: string): string | null; setItem(key: string, value: string): void; }
export const ADMIN_STORAGE_KEY = 'bagstore.admin-products.v1';
const categories = ['Tote', 'Crossbody', 'Mini'];
const hex = /^#[0-9a-f]{6}$/i;
export function validProductPhoto(value: unknown): value is string {
  return typeof value === 'string' && value.length <= 600000 && /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(value);
}

export function validateProduct(draft: ProductDraft, allowedCategories = categories): DraftErrors {
  const errors: DraftErrors = {};
  if (draft.categoryId !== undefined && !/^[a-z0-9-]+$/.test(draft.categoryId)) errors.category = 'La categoría seleccionada no es válida.';
  if (draft.colorId !== undefined && !/^[a-z0-9-]+$/.test(draft.colorId)) errors.label = 'El color seleccionado no es válido.';
  if (draft.imageData !== undefined && !validProductPhoto(draft.imageData)) errors.imageData = 'La foto no es válida o excede el tamaño de guardado.';
  if (draft.imageName !== undefined && (typeof draft.imageName !== 'string' || draft.imageName.length > 120)) errors.imageName = 'El nombre de la imagen es demasiado largo.';
  if (draft.name.trim().length < 3 || draft.name.trim().length > 80) errors.name = 'Escribe un nombre de 3 a 80 caracteres.';
  if (!allowedCategories.includes(draft.category)) errors.category = 'Selecciona una categoría de la lista.';
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
  for (const key of ['categoryId', 'colorId']) if (p[key] !== undefined && (typeof p[key] !== 'string' || !/^[a-z0-9-]+$/.test(p[key] as string))) return false;
  if (String(p.category).trim().length < 2 || String(p.category).length > 40) return false;
  return Object.keys(validateProduct({ name: p.name as string, category: p.category as string, label: p.label as string, color: p.color as string, accent: p.accent as string, price: String(p.price), imageData: p.imageData as string | undefined, imageName: p.imageName as string | undefined }, [p.category as string])).length === 0;
}

/** Repositorio exclusivo de la demostración administrativa. No representa una API. */
export function createProductRepository(seed: Product[], storage?: DemoStorage, allowedCategories: () => string[] = () => categories) {
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
    bindCatalogs(resolve: (product: AdminProduct) => { categoryId?: string; colorId?: string }) {
      let changed = false;
      for (const p of items) {
        const refs = resolve({ ...p });
        for (const key of ['categoryId', 'colorId'] as const) if (refs[key] && refs[key] !== p[key]) { p[key] = refs[key]; changed = true; }
      }
      if (changed) persist();
    },
    save(draft: ProductDraft, id?: number): AdminProduct {
      if (Object.keys(validateProduct(draft, allowedCategories())).length) throw new Error('Revisa los campos del producto.');
      const index = id === undefined ? -1 : items.findIndex(p => p.id === id);
      if (id !== undefined && index === -1) throw new Error('El producto ya no está disponible en la demostración.');
      const product: AdminProduct = {
        id: id ?? Math.max(0, ...items.map(p => p.id)) + 1,
        active: index >= 0 ? items[index].active : true,
        name: draft.name.trim(), category: draft.category as Product['category'], label: draft.label.trim(),
        color: draft.color, accent: draft.accent, price: Number(draft.price),
        ...(draft.categoryId ? { categoryId: draft.categoryId } : {}), ...(draft.colorId ? { colorId: draft.colorId } : {}),
        ...(draft.imageData ? { imageData: draft.imageData, imageName: draft.imageName ?? 'Foto del producto' } : {})
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
