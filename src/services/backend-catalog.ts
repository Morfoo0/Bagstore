import { ApiClient, ApiError } from './api';
export type State = 'activo' | 'inactivo';
export interface CategoryDTO { id: number; nombre: string; slug: string; descripcion?: string | null; estado: State; orden: number; total_productos: number; }
export interface CollectionDTO { id: number; nombre: string; slug: string; descripcion?: string | null; estado: State; imagen_portada_url?: string | null; total_productos: number; }
export interface ImageDTO { url: string; texto_alternativo: string | null; orden: number; es_principal: boolean; }
export interface ProductSummary { id: number; nombre: string; slug: string; precio: number; disponible: boolean; estado: State; categoria: {id: number; nombre: string; slug: string}; imagen_principal: ImageDTO | null; }
export interface ProductDTO extends ProductSummary { descripcion: string | null; sku: string; existencias: number; imagenes: ImageDTO[]; colecciones: {id: number; nombre: string; slug: string}[]; }
export interface ProductWrite { nombre: string; descripcion: string | null; precio: number; sku?: string; categoria_id: number; existencias: number; estado: State; imagenes: ImageDTO[]; }
export interface CategoryWrite { nombre: string; descripcion: string | null; orden: number; estado: State; }
export interface CollectionWrite { nombre: string; descripcion: string | null; estado: State; imagen_portada_url: string | null; producto_ids: number[]; }
export interface Page<T> { datos: T[]; paginacion: {pagina: number; por_pagina: number; total: number; total_paginas: number}; }
const object = (v: unknown): v is Record<string, any> => !!v && typeof v === 'object' && !Array.isArray(v);
const positive = (v: unknown): v is number => Number.isSafeInteger(v) && Number(v) > 0;
const nonnegative = (v: unknown): v is number => Number.isSafeInteger(v) && Number(v) >= 0;
const text = (v: unknown): v is string => typeof v === 'string';
const state = (v: unknown) => v === 'activo' || v === 'inactivo';
export function httpImage(v: unknown): v is string { if (!text(v) || v.length > 500) return false; try { const u = new URL(v); return ['http:', 'https:'].includes(u.protocol) && !u.username && !u.password; } catch { return false; } }
const image = (v: unknown): v is ImageDTO => object(v) && httpImage(v.url) && (v.texto_alternativo === null || text(v.texto_alternativo)) && nonnegative(v.orden) && typeof v.es_principal === 'boolean';
const named = (v: unknown): boolean => object(v) && positive(v.id) && text(v.nombre) && text(v.slug);
const nullableText = (v: unknown) => v === undefined || v === null || text(v);
const category = (v: unknown): v is CategoryDTO => named(v) && object(v) && state(v.estado) && nonnegative(v.orden) && nonnegative(v.total_productos) && nullableText(v.descripcion);
const collection = (v: unknown): v is CollectionDTO => named(v) && object(v) && state(v.estado) && nonnegative(v.total_productos) && nullableText(v.descripcion) && (v.imagen_portada_url == null || httpImage(v.imagen_portada_url));
const summary = (v: unknown): v is ProductSummary => named(v) && object(v) && Number.isFinite(v.precio) && v.precio > 0 && typeof v.disponible === 'boolean' && state(v.estado) && named(v.categoria) && (v.imagen_principal === null || image(v.imagen_principal));
// El detalle no incluye imagen_principal: se deriva de imagenes.
function product(v: unknown): ProductDTO {
  if (!object(v) || !Array.isArray(v.imagenes) || !v.imagenes.every(image)) throw invalid();
  const value = {...v, imagen_principal: v.imagenes.find((i: ImageDTO) => i.es_principal) ?? v.imagenes[0] ?? null};
  if (!summary(value) || !text(v.sku) || !nullableText(v.descripcion) || !nonnegative(v.existencias) || v.disponible !== (v.existencias > 0) || !Array.isArray(v.colecciones) || !v.colecciones.every(named)) throw invalid();
  return value as ProductDTO;
}
function invalid() { return new ApiError('La respuesta del catálogo no tiene el formato esperado. Inténtalo de nuevo o contacta al equipo.'); }
function page<T>(v: unknown, check: (v: unknown) => v is T): Page<T> {
  if (!object(v) || !Array.isArray(v.datos) || !v.datos.every(check) || !object(v.paginacion) || !positive(v.paginacion.pagina) || !positive(v.paginacion.por_pagina) || v.paginacion.por_pagina > 100 || !nonnegative(v.paginacion.total) || !nonnegative(v.paginacion.total_paginas)) throw invalid();
  return v as Page<T>;
}
export type Query = Record<string, string | number | boolean | undefined>;
function query(values: Query) { const q = new URLSearchParams(); for (const [key,value] of Object.entries(values)) if (value !== undefined && value !== '') q.set(key, String(value)); return q.size ? `?${q}` : ''; }
export class BackendCatalog {
  private client: ApiClient;
  constructor(client: ApiClient) { this.client = client; }
  products = async (filters: Query = {}) => page(await this.client.request(`/api/productos${query(filters)}`), summary);
  categories = async (filters: Query = {}) => page(await this.client.request(`/api/categorias${query(filters)}`), category);
  collections = async (filters: Query = {}) => page(await this.client.request(`/api/colecciones${query(filters)}`), collection);
  product = async (id: number) => product(await this.client.request(`/api/productos/${validId(id)}`));
  category = async (id: number) => checked(await this.client.request(`/api/categorias/${validId(id)}`), category);
  collection = async (id: number) => checked(await this.client.request(`/api/colecciones/${validId(id)}`), collection);
  saveProduct = async (value: ProductWrite, id?: number) => {
    if (!value.nombre.trim() || value.nombre.length > 150 || !Number.isFinite(value.precio) || value.precio <= 0 || value.precio > 999999.99 || Math.abs(value.precio * 100 - Math.round(value.precio * 100)) > 1e-6 || !positive(value.categoria_id) || !nonnegative(value.existencias) || value.existencias > 1000000 || !state(value.estado) || (value.descripcion?.length ?? 0) > 5000 || value.imagenes.length > 10 || !value.imagenes.every(image) || new Set(value.imagenes.map(i=>i.orden)).size !== value.imagenes.length || value.imagenes.filter(i=>i.es_principal).length > 1 || (id === undefined && !/^[A-Z0-9]+(?:-[A-Z0-9]+)*$/.test(value.sku ?? '')) || (value.sku !== undefined && (value.sku.length < 3 || value.sku.length > 50))) throw new ApiError('Revisa nombre, SKU, precio, categoría, existencias e imágenes.');
    // Lista blanca: nunca enviar colores locales, data URLs o campos derivados.
    const body = {nombre:value.nombre.trim(), descripcion:value.descripcion, precio:value.precio, categoria_id:value.categoria_id, existencias:value.existencias, estado:value.estado, imagenes:value.imagenes, ...(id === undefined ? {sku:value.sku} : {})};
    return product(await this.client.request(`/api/productos${id === undefined ? '' : '/' + validId(id)}`, {method:id === undefined ? 'POST':'PUT', body:JSON.stringify(body)}));
  };
  saveCategory = async (v: CategoryWrite, id?: number) => checked(await this.client.request(`/api/categorias${id === undefined ? '' : '/' + validId(id)}`, {method:id === undefined?'POST':'PUT', body:JSON.stringify({nombre:v.nombre,descripcion:v.descripcion,orden:v.orden,estado:v.estado})}), category);
  saveCollection = async (v: CollectionWrite, id?: number) => checked(await this.client.request(`/api/colecciones${id === undefined ? '' : '/' + validId(id)}`, {method:id === undefined?'POST':'PUT', body:JSON.stringify({nombre:v.nombre,descripcion:v.descripcion,estado:v.estado,imagen_portada_url:v.imagen_portada_url,producto_ids:[...new Set(v.producto_ids)]})}), collection);
  remove = (resource: 'productos'|'categorias'|'colecciones', id: number) => this.client.request<void>(`/api/${resource}/${validId(id)}`, {method:'DELETE'});
  health = () => this.client.request('/api/health');
}
function checked<T>(v: unknown, check: (v: unknown) => v is T): T { if (!check(v)) throw invalid(); return v; }
function validId(id: number) { if (!positive(id)) throw new ApiError('El identificador no es válido.'); return id; }
