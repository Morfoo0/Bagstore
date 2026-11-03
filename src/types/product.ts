export type Category = 'Todas' | 'Tote' | 'Crossbody' | 'Mini';
export interface Product { id: number; name: string; category: Exclude<Category, 'Todas'>; color: string; accent: string; price: number; label: string; }
