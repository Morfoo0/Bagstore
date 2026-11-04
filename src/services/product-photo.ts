import { validProductPhoto } from './admin-products';

export function validatePhotoFile(type: string, size: number): string | undefined {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(type)) return 'Selecciona una foto JPG, PNG o WebP. No se admiten SVG ni otros archivos.';
  if (size <= 0 || size > 5 * 1024 * 1024) return 'La foto debe pesar como máximo 5 MB y no estar vacía.';
}

/** Preparación local; no sube archivos a ningún servidor. */
export async function prepareProductPhoto(file: File): Promise<{ data: string; name: string }> {
  const error = validatePhotoFile(file.type, file.size);
  if (error) throw new Error(error);
  const url = URL.createObjectURL(file);
  try {
    const image = new Image();
    image.src = url;
    await image.decode();
    if (!image.naturalWidth || !image.naturalHeight || image.naturalWidth * image.naturalHeight > 30000000) throw new Error('La foto tiene dimensiones demasiado grandes. Usa una imagen de hasta 30 megapíxeles.');
    const ratio = Math.min(1, 700 / Math.max(image.naturalWidth, image.naturalHeight));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(image.naturalWidth * ratio));
    canvas.height = Math.max(1, Math.round(image.naturalHeight * ratio));
    const context = canvas.getContext('2d');
    if (!context) throw new Error('No pudimos preparar la imagen en este navegador.');
    context.fillStyle = '#FAF7F0';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const data = canvas.toDataURL('image/jpeg', 0.82);
    if (!validProductPhoto(data)) throw new Error('La imagen sigue siendo demasiado pesada. Prueba con una foto más pequeña.');
    return { data, name: file.name.slice(0, 120) };
  } catch (error) {
    if (error instanceof Error && error.name !== 'EncodingError') throw error;
    throw new Error('No pudimos leer esta foto. Revisa que el archivo sea una imagen válida.');
  } finally { URL.revokeObjectURL(url); }
}
