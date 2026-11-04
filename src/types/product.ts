export type Category = string;
export interface Product { id: number; name: string; category: string; categoryId?: string; colorId?: string; color: string; accent: string; price: number; label: string; imageData?: string; imageName?: string; }
