export function escapeHtml(value: string): string { return value.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!); }
export function money(value: number): string { return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2 }).format(value); }
export function element<T extends HTMLElement = HTMLElement>(selector: string): T { const node = document.querySelector<T>(selector); if (!node) throw new Error(`Falta ${selector}`); return node; }
