import type { ProductDraft } from '../services/admin-products';

/** Producto de prueba solicitado por el usuario. Solo para el panel administrativo. */
export const requestedTestProduct: ProductDraft = {
  name: 'Tote Aurora — prueba',
  category: 'Tote',
  label: 'Beige clásico',
  color: '#CDB89E',
  accent: '#948067',
  price: '529.00'
};
export const testProductRequestKey = 'bagstore.demo-request.aurora.v1';
