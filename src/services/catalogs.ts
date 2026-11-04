export interface NamedOption { id: string; name: string; }
export interface ColorOption extends NamedOption { tone: string; }
interface CatalogStorage { getItem(key: string): string | null; setItem(key: string, value: string): void; }
export const CATALOG_KEY = 'bagstore.catalogs.v1';
export const baseCategories: NamedOption[] = [{ id: 'cat-tote', name: 'Tote' }, { id: 'cat-crossbody', name: 'Crossbody' }, { id: 'cat-mini', name: 'Mini' }];
export const baseColors: ColorOption[] = [
  ['negro', 'Negro', '#252220'], ['blanco', 'Blanco', '#FFFFFF'], ['beige', 'Beige', '#CDB89E'], ['cafe', 'Café', '#805839'], ['rojo', 'Rojo', '#B83236'],
  ['rosa', 'Rosa', '#DFA8B8'], ['azul', 'Azul', '#456A97'], ['verde', 'Verde', '#71836B'], ['gris', 'Gris', '#989898'], ['multicolor', 'Multicolor', '#B28AAB']
].map(([id, name, tone]) => ({ id: `color-${id}`, name, tone }));
export function normalizedName(value: string): string { return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().replace(/\s+/g, ' ').toLocaleLowerCase('es'); }
export function legacyColorId(label: string): string | undefined {
  const key = normalizedName(label);
  if (['arena', 'lino', 'beige clasico'].includes(key)) return 'color-beige';
  if (['caramelo', 'cacao', 'chocolate', 'marron'].includes(key)) return 'color-cafe';
  return baseColors.find(c => normalizedName(c.name) === key)?.id;
}
export type CatalogRepository = ReturnType<typeof createCatalogRepository>;
export function createCatalogRepository(storage?: CatalogStorage) {
  let categories = baseCategories.map(c => ({ ...c }));
  let colors = baseColors.map(c => ({ ...c }));
  let warning = '';
  function validName(name: unknown): name is string { return typeof name === 'string' && name.trim().length >= 2 && name.trim().length <= 40; }
  function validList(value: unknown, color: boolean): boolean {
    return Array.isArray(value) && value.length > 0 && value.every(c => c && typeof c.id === 'string' && /^[a-z0-9-]+$/.test(c.id) && validName(c.name) && (!color || /^#[0-9a-f]{6}$/i.test(c.tone))) && new Set(value.map(c => c.id)).size === value.length && new Set(value.map(c => normalizedName(c.name))).size === value.length;
  }
  try {
    const raw = storage?.getItem(CATALOG_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (!validList(parsed.categories, false) || !validList(parsed.colors, true)) throw new Error();
      if (!baseCategories.every(c => parsed.categories.some((v: NamedOption) => v.id === c.id)) || !baseColors.every(c => parsed.colors.some((v: ColorOption) => v.id === c.id))) throw new Error();
      categories = parsed.categories; colors = parsed.colors;
    }
  } catch { warning = 'No se pudieron recuperar los catálogos guardados. Se usan las opciones básicas.'; }
  function persist() {
    try { if (!storage) throw new Error(); storage.setItem(CATALOG_KEY, JSON.stringify({ categories, colors })); warning = ''; }
    catch { warning = 'Los catálogos cambiaron en memoria, pero no se pudieron guardar en este navegador.'; }
  }
  function nameFor(list: NamedOption[], name: string, except?: string) {
    if (!validName(name)) throw new Error('Escribe un nombre de 2 a 40 caracteres.');
    const clean = name.trim().replace(/\s+/g, ' ');
    if (list.some(c => c.id !== except && normalizedName(c.name) === normalizedName(clean))) throw new Error('Ese nombre ya existe. Selecciona la opción disponible.');
    return clean;
  }
  function nextId(prefix: string, list: NamedOption[]) { let n = list.length + 1; while (list.some(c => c.id === `${prefix}-${n}`)) n++; return `${prefix}-${n}`; }
  return {
    categories: () => categories.map(c => ({ ...c })), colors: () => colors.map(c => ({ ...c })), warning: () => warning,
    addCategory(name: string) { const option = { id: nextId('cat', categories), name: nameFor(categories, name) }; categories.push(option); persist(); return { ...option }; },
    renameCategory(id: string, name: string) { const option = categories.find(c => c.id === id); if (!option) throw new Error('Categoría no encontrada.'); option.name = nameFor(categories, name, id); persist(); return { ...option }; },
    addColor(name: string, tone: string) { if (!/^#[0-9a-f]{6}$/i.test(tone)) throw new Error('Selecciona un tono válido.'); const option = { id: nextId('color', colors), name: nameFor(colors, name), tone }; colors.push(option); persist(); return { ...option }; }
  };
}
