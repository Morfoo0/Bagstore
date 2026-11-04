# Contrato de API — Módulo de Catálogo (BagStore)

**Versión del contrato:** 0.2.0 (borrador)
**Estado:** Revisión técnica y reglas de acceso incorporadas. Sin implementación.
**Base URL de desarrollo:** `http://localhost:8000`
**Prefijo:** `/api`
**Formato:** JSON UTF-8
**Acceso:** Rol único `administrador`. Los visitantes consultan el catálogo activo mediante `GET`. Todas las escrituras requieren autenticación y rol `administrador`; el mecanismo de autenticación se implementará en una fase posterior.

---

## Tabla de contenidos

1. [Alcance](#1-alcance)
2. [Convenciones](#2-convenciones)
3. [Resumen de endpoints](#3-resumen-de-endpoints)
4. [Productos](#4-productos)
5. [Categorías](#5-categorías)
6. [Colecciones](#6-colecciones)
7. [Formato de errores](#7-formato-de-errores)
8. [Códigos HTTP](#8-códigos-http)
9. [Validaciones transversales](#9-validaciones-transversales)
10. [Decisiones pendientes del responsable de Base de Datos](#10-decisiones-pendientes-del-responsable-de-base-de-datos)
11. [Información requerida del responsable de Frontend](#11-información-requerida-del-responsable-de-frontend)
12. [Compatibilidad y consideraciones](#12-compatibilidad-y-consideraciones)
13. [Fuera de alcance](#13-fuera-de-alcance)

---

## 1. Alcance

Este documento define el contrato REST del módulo de catálogo:

- CRUD de productos.
- CRUD de categorías.
- CRUD de colecciones.
- Filtros y paginación de productos.
- Reglas de acceso para visitantes y administradores.
- Validaciones, códigos HTTP y formato de errores.

El frontend existente cuenta con las secciones: Inicio, Todas las bolsas, Tote Bags, Cross Body, Mini Bags, La Colección y Sección de Ayuda.

- "Todas las bolsas" corresponde a un listado sin filtro de categoría.
- "Tote Bags", "Cross Body" y "Mini Bags" corresponden a categorías.
- "La Colección" **no es una categoría**: es una colección cuyos productos pueden pertenecer a distintas categorías.
- "Inicio" y "Sección de Ayuda" no forman parte de este contrato.

> **Nota:** Los nombres, slugs y relaciones de este documento son propuestas. Las decisiones marcadas como pendientes deben validarse con el responsable de Base de Datos antes de implementar.

### 1.1 Control de acceso

BagStore tendrá un único rol: `administrador`.

| Actor | Permisos |
|---|---|
| Visitante | `GET` de productos, categorías y colecciones; únicamente recursos activos. |
| Administrador | `GET` completo (incluye recursos inactivos) y operaciones `POST`, `PUT` y `DELETE`. |

Reglas:

- La autenticación y la autorización se implementarán en una fase posterior. Este contrato define el comportamiento esperado.
- Todas las operaciones de escritura (`POST`, `PUT`, `DELETE`) requieren credenciales válidas y rol `administrador`.
- Sin credenciales válidas o con credenciales inválidas: `401 NO_AUTENTICADO`.
- Con credenciales válidas pero sin rol `administrador`: `403 ACCESO_DENEGADO`.
- Un visitante que solicite `estado=inactivo` o `estado=todos` recibe `403 ACCESO_DENEGADO`.
- Un visitante que solicite por ID un producto, categoría o colección inactiva recibe `404 RECURSO_NO_ENCONTRADO` para no revelar su existencia.
- El orden de validación es: autenticación, autorización, validación de datos y existencia del recurso.
- **Ocultar botones u opciones en el frontend no sustituye la validación de permisos en el backend.** Cada endpoint de escritura debe verificar la autenticación y el rol del lado servidor.
- CORS controla qué orígenes pueden llamar desde el navegador; no es un mecanismo de autorización.

---

## 2. Convenciones

| Convención | Definición |
|---|---|
| Nombres de campos | `snake_case` en español |
| Rutas | Sustantivos en plural y español: `/api/productos`, `/api/categorias`, `/api/colecciones` |
| Versionado | Sin `/v1` en esta fase, para no romper el frontend actual |
| Identificadores | Enteros positivos (propuesta pendiente de BD) |
| Fechas | ISO 8601 en UTC, por ejemplo `2026-11-03T18:00:00Z` |
| Dinero | `precio` como número decimal con dos decimales (propuesta pendiente de BD) |
| Listados | Envoltura `datos` + `paginacion` |
| Errores | Envoltura única `error` |
| `PUT` | Reemplazo completo del recurso, con campos inmutables y campos obligatorios explícitos |
| `PATCH` | No incluido en este alcance |
| Borrado | Producto: lógico. Categoría y colección: físico con validación de dependencias. `404` después de borrar |
| Inmutables | `id` y `creado_en`; `sku` en productos |

---

## 3. Resumen de endpoints

| Recurso | Método | Ruta | Éxito | Acceso |
|---|---|---|---|---|
| Productos | GET | `/api/productos` | 200 | Público (solo activos) / Administrador (todos) |
| Productos | GET | `/api/productos/{id}` | 200 | Público (solo activo) / Administrador |
| Productos | POST | `/api/productos` | 201 | Administrador |
| Productos | PUT | `/api/productos/{id}` | 200 | Administrador |
| Productos | DELETE | `/api/productos/{id}` | 204 | Administrador |
| Categorías | GET | `/api/categorias` | 200 | Público (solo activas) / Administrador (todas) |
| Categorías | GET | `/api/categorias/{id}` | 200 | Público (solo activa) / Administrador |
| Categorías | POST | `/api/categorias` | 201 | Administrador |
| Categorías | PUT | `/api/categorias/{id}` | 200 | Administrador |
| Categorías | DELETE | `/api/categorias/{id}` | 204 | Administrador |
| Colecciones | GET | `/api/colecciones` | 200 | Público (solo activas) / Administrador (todas) |
| Colecciones | GET | `/api/colecciones/{id}` | 200 | Público (solo activa) / Administrador |
| Colecciones | POST | `/api/colecciones` | 201 | Administrador |
| Colecciones | PUT | `/api/colecciones/{id}` | 200 | Administrador |
| Colecciones | DELETE | `/api/colecciones/{id}` | 204 | Administrador |

---

## 4. Productos

### 4.1 Campos

| Campo | Tipo | Obligatorio | Origen | Reglas |
|---|---|---|---|---|
| `id` | entero | Sí (respuesta) | Servidor | Positivo, inmutable |
| `nombre` | string | Sí | Solicitud | 2 a 150 caracteres, sin espacios extremos |
| `slug` | string | No | Solicitud / Servidor | Único; se genera desde `nombre` si se omite en `POST`; si se omite en `PUT`, conserva el actual |
| `descripcion` | string | No | Solicitud | Máximo 5000 caracteres |
| `precio` | decimal | Sí | Solicitud | Mayor que 0, máximo 999999.99, dos decimales |
| `sku` | string | Sí en `POST` | Solicitud | Único, 3 a 50 caracteres, mayúsculas, números y guiones; inmutable después de crear |
| `categoria_id` | entero | Sí | Solicitud | Debe existir y estar activa si el producto está activo |
| `categoria` | objeto | Sí (respuesta) | Servidor | `{id, nombre, slug}` |
| `colecciones` | objeto[] | Sí (respuesta) | Servidor | `[{id, nombre, slug}]`; solo lectura, se administra desde colecciones |
| `existencias` | entero | Sí | Solicitud | Mayor o igual a 0; valor absoluto, no incremento |
| `disponible` | booleano | Sí (respuesta) | Servidor | `true` cuando `existencias > 0` |
| `imagenes` | objeto[] | No en `POST`; obligatorio en `PUT` | Solicitud | Máximo 10; ver estructura |
| `estado` | enum | No | Solicitud | `activo` o `inactivo`; por defecto `activo` en `POST`; obligatorio en `PUT` |
| `creado_en` | datetime | Sí (respuesta) | Servidor | UTC, inmutable |
| `actualizado_en` | datetime | Sí (respuesta) | Servidor | UTC |

> **Existencias:** en esta fase se administran manualmente desde el catálogo. No se descuentan automáticamente al comprar ni existen reservas o inventario por variante. `PUT` establece el valor absoluto y la última escritura gana.

Estructura de cada objeto de `imagenes`:

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `url` | string | Sí | URL válida `http` o `https`, máximo 500 caracteres |
| `texto_alternativo` | string | No | Máximo 150 caracteres |
| `orden` | entero | No | Mayor o igual a 0; sin duplicados dentro del producto; si se omite, se asigna por posición |
| `es_principal` | booleano | No | Máximo una imagen con `true`; si ninguna lo indica, la primera será la principal |

### 4.1.1 `ProductoResumen` (listados)

Los listados devuelven un resumen para tarjetas de catálogo:

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | entero | Positivo |
| `nombre` | string | — |
| `slug` | string | — |
| `precio` | decimal | Dos decimales |
| `disponible` | booleano | Derivado de `existencias` |
| `estado` | enum | `activo` o `inactivo` |
| `imagen_principal` | objeto o `null` | Imagen marcada como principal o `null` si no hay imágenes |
| `categoria` | objeto | `{id, nombre, slug}` |

### 4.2 Filtros de listado

`GET /api/productos`

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `categoria` | string | — | Slug de categoría. Ejemplo: `tote-bags` |
| `categoria_id` | entero | — | ID de categoría. No puede combinarse con `categoria` |
| `nombre` | string | — | Búsqueda parcial por nombre, sin distinguir mayúsculas |
| `disponible` | booleano | — | `true`: existencias > 0. `false`: existencias = 0 |
| `coleccion` | string | — | Slug de colección. Ejemplo: `la-coleccion` |
| `coleccion_id` | entero | — | ID de colección. No puede combinarse con `coleccion` |
| `estado` | string | `activo` | `activo`; `inactivo` y `todos` requieren administrador |
| `pagina` | entero | `1` | Mayor o igual a 1 |
| `por_pagina` | entero | `20` | Entre 1 y 100 |
| `orden` | string | `reciente` | `reciente`, `nombre_asc`, `nombre_desc`, `precio_asc`, `precio_desc` |

Reglas de filtros:

- Si se envían `categoria` y `categoria_id` a la vez: `400 SOLICITUD_INVALIDA`.
- Si se envían `coleccion` y `coleccion_id` a la vez: `400 SOLICITUD_INVALIDA`.
- Los filtros por colección incluyen productos de cualquier categoría.
- Un visitante solo puede usar `estado=activo`; si solicita `inactivo` o `todos`: `403 ACCESO_DENEGADO`.
- Los filtros públicos solo consideran categorías y colecciones activas; un slug inactivo no devuelve productos.
- Por defecto solo se devuelven productos con `estado=activo`.
- El administrador puede usar `estado=inactivo` o `estado=todos`.

### 4.3 GET `/api/productos`

Solicitud:

```http
GET /api/productos?categoria=tote-bags&nombre=aurora&disponible=true&coleccion=la-coleccion&pagina=1&por_pagina=20&orden=precio_asc
```

Respuesta `200 OK`:

```json
{
  "datos": [
    {
      "id": 12,
      "nombre": "Tote Bag Aurora",
      "slug": "tote-bag-aurora",
      "precio": 899.00,
      "disponible": true,
      "estado": "activo",
      "imagen_principal": {
        "url": "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
        "texto_alternativo": "Tote Bag Aurora",
        "orden": 1,
        "es_principal": true
      },
      "categoria": {
        "id": 2,
        "nombre": "Tote Bags",
        "slug": "tote-bags"
      }
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 1,
    "total_paginas": 1
  }
}
```

Si el producto no tiene imágenes, `imagen_principal` es `null`.

### 4.4 GET `/api/productos/{id}`

Solicitud:

```http
GET /api/productos/12
```

Respuesta `200 OK`:

```json
{
  "id": 12,
  "nombre": "Tote Bag Aurora",
  "slug": "tote-bag-aurora",
  "descripcion": "Tote bag de lona con asas reforzadas.",
  "precio": 899.00,
  "sku": "BAG-TOT-001",
  "categoria": {
    "id": 2,
    "nombre": "Tote Bags",
    "slug": "tote-bags"
  },
  "colecciones": [
    {
      "id": 1,
      "nombre": "La Colección",
      "slug": "la-coleccion"
    }
  ],
  "existencias": 12,
  "disponible": true,
  "imagenes": [
    {
      "url": "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
      "texto_alternativo": "Tote Bag Aurora",
      "orden": 1,
      "es_principal": true
    },
    {
      "url": "https://cdn.bagstore.com/productos/tote-aurora-2.jpg",
      "texto_alternativo": "Tote Bag Aurora vista lateral",
      "orden": 2,
      "es_principal": false
    }
  ],
  "estado": "activo",
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-03T18:00:00Z"
}
```

Si el producto está inactivo:

- Visitante: `404 RECURSO_NO_ENCONTRADO`.
- Administrador: `200 OK`.

Respuesta `404 Not Found` para visitante:

```json
{
  "error": {
    "codigo": "RECURSO_NO_ENCONTRADO",
    "mensaje": "No existe un producto con id 999.",
    "detalles": []
  }
}
```

### 4.5 POST `/api/productos`

Solicitud:

```http
POST /api/productos
Content-Type: application/json
```

```json
{
  "nombre": "Tote Bag Aurora",
  "slug": "tote-bag-aurora",
  "descripcion": "Tote bag de lona con asas reforzadas.",
  "precio": 899.00,
  "sku": "BAG-TOT-001",
  "categoria_id": 2,
  "existencias": 12,
  "imagenes": [
    {
      "url": "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
      "texto_alternativo": "Tote Bag Aurora",
      "orden": 1,
      "es_principal": true
    }
  ],
  "estado": "activo"
}
```

> Las colecciones no se asignan desde el producto. Para agregarlo a una colección se usa `PUT /api/colecciones/{id}` con `producto_ids`.

Respuesta `201 Created`:

Cabecera: `Location: /api/productos/12`

```json
{
  "id": 12,
  "nombre": "Tote Bag Aurora",
  "slug": "tote-bag-aurora",
  "descripcion": "Tote bag de lona con asas reforzadas.",
  "precio": 899.00,
  "sku": "BAG-TOT-001",
  "categoria": {
    "id": 2,
    "nombre": "Tote Bags",
    "slug": "tote-bags"
  },
  "colecciones": [],
  "existencias": 12,
  "disponible": true,
  "imagenes": [
    {
      "url": "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
      "texto_alternativo": "Tote Bag Aurora",
      "orden": 1,
      "es_principal": true
    }
  ],
  "estado": "activo",
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-03T18:00:00Z"
}
```

### 4.6 PUT `/api/productos/{id}`

`PUT` reemplaza el recurso completo. Reglas:

- Campos obligatorios: `nombre`, `precio`, `categoria_id`, `existencias`, `estado` e `imagenes` (puede ser `[]`).
- `sku` es inmutable. Puede omitirse; si se envía, debe ser idéntico al actual. Un cambio devuelve `422 VALIDACION_FALLIDA`.
- `slug` es opcional. Si se omite, conserva el actual. Si se cambia, el anterior deja de funcionar y puede romper enlaces.
- `descripcion` omitida se establece en `null`.
- Si se envía `imagenes: []`, se eliminan todas las imágenes. El cliente debe enviar siempre el arreglo completo.
- `estado` es obligatorio para evitar reactivar un producto inactivo por omisión.
- Las colecciones no se modifican desde el producto; se administran desde `/api/colecciones`.
- No existe `PATCH`. No hay bloqueo optimista: la última escritura gana.

Solicitud:

```http
PUT /api/productos/12
Content-Type: application/json
```

```json
{
  "nombre": "Tote Bag Aurora",
  "slug": "tote-bag-aurora",
  "descripcion": "Tote bag de lona con asas reforzadas y cierre superior.",
  "precio": 949.00,
  "sku": "BAG-TOT-001",
  "categoria_id": 2,
  "existencias": 8,
  "imagenes": [
    {
      "url": "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
      "texto_alternativo": "Tote Bag Aurora",
      "orden": 1,
      "es_principal": true
    }
  ],
  "estado": "activo"
}
```

Respuesta `200 OK`:

```json
{
  "id": 12,
  "nombre": "Tote Bag Aurora",
  "slug": "tote-bag-aurora",
  "descripcion": "Tote bag de lona con asas reforzadas y cierre superior.",
  "precio": 949.00,
  "sku": "BAG-TOT-001",
  "categoria": {
    "id": 2,
    "nombre": "Tote Bags",
    "slug": "tote-bags"
  },
  "colecciones": [
    {
      "id": 1,
      "nombre": "La Colección",
      "slug": "la-coleccion"
    }
  ],
  "existencias": 8,
  "disponible": true,
  "imagenes": [
    {
      "url": "https://cdn.bagstore.com/productos/tote-aurora-1.jpg",
      "texto_alternativo": "Tote Bag Aurora",
      "orden": 1,
      "es_principal": true
    }
  ],
  "estado": "activo",
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-04T10:30:00Z"
}
```

### 4.7 DELETE `/api/productos/{id}`

Solicitud:

```http
DELETE /api/productos/12
```

Respuesta `204 No Content` (sin cuerpo).

El borrado es lógico:

- Tras `204`, `GET /api/productos/{id}` devuelve `404` para cualquier actor.
- El producto desaparece de listados y de colecciones.
- Sus relaciones con colecciones se eliminan.
- `sku` y `slug` quedan reservados y no pueden reutilizarse.
- Un segundo `DELETE` devuelve `404`.
- Para retirar un producto de la venta sin borrarlo, usar `estado=inactivo`.

Respuesta `404 Not Found`:

```json
{
  "error": {
    "codigo": "RECURSO_NO_ENCONTRADO",
    "mensaje": "No existe un producto con id 12.",
    "detalles": []
  }
}
```

### 4.8 Validaciones de productos

| Campo | Validación |
|---|---|
| `nombre` | Obligatorio, 2-150 caracteres, recortar espacios, rechazar solo espacios |
| `slug` | Opcional; minúsculas, sin acentos, solo `a-z`, `0-9` y guiones; único; en `PUT` si se omite conserva el actual |
| `descripcion` | Opcional, máximo 5000 caracteres |
| `precio` | Obligatorio, mayor que 0, máximo 999999.99, máximo dos decimales, valor finito |
| `sku` | Obligatorio en `POST`; 3-50 caracteres; `^[A-Z0-9]+(?:-[A-Z0-9]+)*$`; único sin distinguir mayúsculas; inmutable en `PUT` |
| `categoria_id` | Obligatorio, entero positivo, debe existir y estar activa si el producto está activo |
| `existencias` | Obligatorio, entero entre 0 y 1,000,000; valor absoluto |
| `imagenes` | Opcional en `POST`; obligatorio en `PUT`; máximo 10; URL válida; `orden` sin duplicados; máximo una imagen principal; vacío permitido |
| `estado` | Solo `activo` o `inactivo`; obligatorio en `PUT` |
| Cuerpo | Rechazar campos desconocidos para evitar asignación masiva |
| Inmutables | `id`, `sku`, `creado_en` |

Reglas de negocio:

- Un producto activo no puede pertenecer a una categoría inactiva.
- `disponible` no es editable: se calcula desde `existencias`.
- Un producto puede pertenecer a cero, una o varias colecciones.
- Las colecciones se administran desde `/api/colecciones`; `colecciones` en el producto es de solo lectura.
- No se permite modificar el `sku` después de crear el producto.
- Si se omite `slug` en `PUT`, se conserva el actual; si se cambia, los enlaces anteriores dejan de ser válidos.

---

## 5. Categorías

### 5.1 Campos

| Campo | Tipo | Obligatorio | Origen | Reglas |
|---|---|---|---|---|
| `id` | entero | Sí (respuesta) | Servidor | Positivo, inmutable |
| `nombre` | string | Sí | Solicitud | 2 a 80 caracteres, único sin distinguir mayúsculas |
| `slug` | string | No | Solicitud / Servidor | Único; se genera desde `nombre` si se omite en `POST`; si se omite en `PUT`, conserva el actual |
| `descripcion` | string | No | Solicitud | Máximo 1000 caracteres |
| `estado` | enum | No en `POST`; obligatorio en `PUT` | Solicitud | `activo` o `inactivo`; por defecto `activo` |
| `orden` | entero | No | Solicitud | Mayor o igual a 0; para ordenar secciones |
| `total_productos` | entero | Sí (respuesta) | Servidor | Visitante: solo activos. Administrador: todos |
| `creado_en` | datetime | Sí (respuesta) | Servidor | UTC |
| `actualizado_en` | datetime | Sí (respuesta) | Servidor | UTC |

Categorías iniciales propuestas (pendientes de confirmar slugs):

- `tote-bags` — Tote Bags
- `cross-body` — Cross Body
- `mini-bags` — Mini Bags

"Todas las bolsas" no se modela como categoría. "La Colección" tampoco: es una colección.

`total_productos` no cuenta productos con borrado lógico.

### 5.2 GET `/api/categorias`

Filtros: `nombre` (parcial), `estado` (`activo` por defecto; `inactivo` y `todos` requieren administrador), `pagina`, `por_pagina`.

Solicitud:

```http
GET /api/categorias?estado=activo&pagina=1&por_pagina=20
```

Respuesta `200 OK`:

```json
{
  "datos": [
    {
      "id": 2,
      "nombre": "Tote Bags",
      "slug": "tote-bags",
      "descripcion": "Bolsas tote.",
      "estado": "activo",
      "orden": 1,
      "total_productos": 8,
      "creado_en": "2026-11-03T18:00:00Z",
      "actualizado_en": "2026-11-03T18:00:00Z"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 1,
    "total_paginas": 1
  }
}
```

### 5.3 GET `/api/categorias/{id}`

Solicitud:

```http
GET /api/categorias/2
```

Respuesta `200 OK`:

```json
{
  "id": 2,
  "nombre": "Tote Bags",
  "slug": "tote-bags",
  "descripcion": "Bolsas tote.",
  "estado": "activo",
  "orden": 1,
  "total_productos": 8,
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-03T18:00:00Z"
}
```

Si la categoría está inactiva:

- Visitante: `404 RECURSO_NO_ENCONTRADO`.
- Administrador: `200 OK`.

### 5.4 POST `/api/categorias`

Solicitud:

```http
POST /api/categorias
Content-Type: application/json
```

```json
{
  "nombre": "Cross Body",
  "slug": "cross-body",
  "descripcion": "Bolsas cross body.",
  "estado": "activo",
  "orden": 2
}
```

Respuesta `201 Created`:

Cabecera: `Location: /api/categorias/3`

```json
{
  "id": 3,
  "nombre": "Cross Body",
  "slug": "cross-body",
  "descripcion": "Bolsas cross body.",
  "estado": "activo",
  "orden": 2,
  "total_productos": 0,
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-03T18:00:00Z"
}
```

### 5.5 PUT `/api/categorias/{id}`

Solicitud:

```http
PUT /api/categorias/3
Content-Type: application/json
```

```json
{
  "nombre": "Cross Body",
  "slug": "cross-body",
  "descripcion": "Bolsas cross body y bandoleras.",
  "estado": "activo",
  "orden": 2
}
```

Respuesta `200 OK`:

```json
{
  "id": 3,
  "nombre": "Cross Body",
  "slug": "cross-body",
  "descripcion": "Bolsas cross body y bandoleras.",
  "estado": "activo",
  "orden": 2,
  "total_productos": 5,
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-04T10:30:00Z"
}
```

Reglas de `PUT`:

- `estado` es obligatorio.
- `slug` si se omite conserva el actual.
- `descripcion` omitida se establece en `null`.
- `orden` omitido se establece en `0`.

Regla de desactivación: si la categoría tiene productos activos, no se puede cambiar a `estado=inactivo`. Respuesta `409 Conflict`:

```json
{
  "error": {
    "codigo": "CONFLICTO_DEPENDENCIAS",
    "mensaje": "No se puede desactivar la categoría porque tiene productos activos.",
    "detalles": []
  }
}
```

### 5.6 DELETE `/api/categorias/{id}`

Solicitud:

```http
DELETE /api/categorias/3
```

Respuesta `204 No Content` (sin cuerpo).

Si la categoría tiene productos asociados, activos, inactivos o con borrado lógico, respuesta `409 Conflict`:

```json
{
  "error": {
    "codigo": "CONFLICTO_DEPENDENCIAS",
    "mensaje": "No se puede eliminar la categoría porque tiene productos asociados.",
    "detalles": []
  }
}
```

El borrado es físico. Un segundo `DELETE` devuelve `404`.

### 5.7 Validaciones de categorías

| Campo | Validación |
|---|---|
| `nombre` | Obligatorio, 2-80 caracteres, único sin distinguir mayúsculas |
| `slug` | Opcional; minúsculas, sin acentos, solo `a-z`, `0-9` y guiones; único; en `PUT` si se omite conserva el actual |
| `descripcion` | Opcional, máximo 1000 caracteres |
| `estado` | Solo `activo` o `inactivo`; obligatorio en `PUT` |
| `orden` | Opcional, entero mayor o igual a 0 |
| Desactivación | No permitir si existen productos activos |
| Borrado | No permitir si existen productos asociados, activos, inactivos o con borrado lógico |

---

## 6. Colecciones

Una colección agrupa productos de distintas categorías. "La Colección" es una colección, no una categoría.

### 6.1 Campos

| Campo | Tipo | Obligatorio | Origen | Reglas |
|---|---|---|---|---|
| `id` | entero | Sí (respuesta) | Servidor | Positivo, inmutable |
| `nombre` | string | Sí | Solicitud | 2 a 100 caracteres, único sin distinguir mayúsculas |
| `slug` | string | No | Solicitud / Servidor | Único; se genera desde `nombre` si se omite en `POST`; si se omite en `PUT`, conserva el actual |
| `descripcion` | string | No | Solicitud | Máximo 2000 caracteres |
| `estado` | enum | No en `POST`; obligatorio en `PUT` | Solicitud | `activo` o `inactivo`; por defecto `activo` |
| `imagen_portada_url` | string | No | Solicitud | URL válida `http` o `https`, máximo 500 caracteres |
| `producto_ids` | entero[] | No en `POST`; obligatorio en `PUT` | Solicitud | Únicos, máximo 200, deben existir y no estar eliminados; única vía de escritura de la relación |
| `total_productos` | entero | Sí (respuesta) | Servidor | Visitante: solo activos. Administrador: todos |
| `creado_en` | datetime | Sí (respuesta) | Servidor | UTC |
| `actualizado_en` | datetime | Sí (respuesta) | Servidor | UTC |

> **Relación producto-colección:** es muchos-a-muchos y se administra únicamente desde la colección mediante `producto_ids`. El producto expone `colecciones` como solo lectura. El orden de los productos dentro de la colección queda pendiente de definir con Base de Datos.

`total_productos` no cuenta productos con borrado lógico.

### 6.2 GET `/api/colecciones`

Filtros: `nombre` (parcial), `estado` (`activo` por defecto; `inactivo` y `todos` requieren administrador), `pagina`, `por_pagina`.

Solicitud:

```http
GET /api/colecciones?estado=activo&pagina=1&por_pagina=20
```

Respuesta `200 OK`:

```json
{
  "datos": [
    {
      "id": 1,
      "nombre": "La Colección",
      "slug": "la-coleccion",
      "descripcion": "Selección especial de temporada.",
      "estado": "activo",
      "imagen_portada_url": "https://cdn.bagstore.com/colecciones/la-coleccion.jpg",
      "total_productos": 12,
      "creado_en": "2026-11-03T18:00:00Z",
      "actualizado_en": "2026-11-03T18:00:00Z"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 1,
    "total_paginas": 1
  }
}
```

### 6.3 GET `/api/colecciones/{id}`

Solicitud:

```http
GET /api/colecciones/1
```

Respuesta `200 OK`:

```json
{
  "id": 1,
  "nombre": "La Colección",
  "slug": "la-coleccion",
  "descripcion": "Selección especial de temporada.",
  "estado": "activo",
  "imagen_portada_url": "https://cdn.bagstore.com/colecciones/la-coleccion.jpg",
  "total_productos": 12,
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-03T18:00:00Z"
}
```

El detalle no incluye productos embebidos. Para obtenerlos, el frontend usa:

```http
GET /api/productos?coleccion=la-coleccion&pagina=1&por_pagina=20
```

Si la colección está inactiva:

- Visitante: `404 RECURSO_NO_ENCONTRADO`.
- Administrador: `200 OK`.

### 6.4 POST `/api/colecciones`

Solicitud:

```http
POST /api/colecciones
Content-Type: application/json
```

```json
{
  "nombre": "La Colección",
  "slug": "la-coleccion",
  "descripcion": "Selección especial de temporada.",
  "estado": "activo",
  "imagen_portada_url": "https://cdn.bagstore.com/colecciones/la-coleccion.jpg",
  "producto_ids": [12, 18]
}
```

Respuesta `201 Created`:

Cabecera: `Location: /api/colecciones/1`

```json
{
  "id": 1,
  "nombre": "La Colección",
  "slug": "la-coleccion",
  "descripcion": "Selección especial de temporada.",
  "estado": "activo",
  "imagen_portada_url": "https://cdn.bagstore.com/colecciones/la-coleccion.jpg",
  "total_productos": 2,
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-03T18:00:00Z"
}
```

### 6.5 PUT `/api/colecciones/{id}`

`PUT` reemplaza la colección. `producto_ids` reemplaza la membresía completa: los productos no incluidos salen de la colección, pero no se eliminan.

Reglas de `PUT`:

- `estado` y `producto_ids` son obligatorios. `producto_ids: []` deja la colección sin productos.
- `slug` si se omite conserva el actual.
- `descripcion` omitida se establece en `null`.
- `imagen_portada_url` omitida se establece en `null`.
- Desactivar una colección no modifica el estado de sus productos.

Solicitud:

```http
PUT /api/colecciones/1
Content-Type: application/json
```

```json
{
  "nombre": "La Colección",
  "slug": "la-coleccion",
  "descripcion": "Selección especial de temporada y ediciones limitadas.",
  "estado": "activo",
  "imagen_portada_url": "https://cdn.bagstore.com/colecciones/la-coleccion-2026.jpg",
  "producto_ids": [12, 18, 21]
}
```

Respuesta `200 OK`:

```json
{
  "id": 1,
  "nombre": "La Colección",
  "slug": "la-coleccion",
  "descripcion": "Selección especial de temporada y ediciones limitadas.",
  "estado": "activo",
  "imagen_portada_url": "https://cdn.bagstore.com/colecciones/la-coleccion-2026.jpg",
  "total_productos": 3,
  "creado_en": "2026-11-03T18:00:00Z",
  "actualizado_en": "2026-11-04T10:30:00Z"
}
```

### 6.6 DELETE `/api/colecciones/{id}`

Solicitud:

```http
DELETE /api/colecciones/1
```

Respuesta `204 No Content` (sin cuerpo).

- El borrado es físico.
- Se eliminan las relaciones con los productos.
- Los productos no se eliminan.
- Un segundo `DELETE` devuelve `404`.
- Para ocultar la colección sin eliminarla, usar `estado=inactivo`.

### 6.7 Validaciones de colecciones

| Campo | Validación |
|---|---|
| `nombre` | Obligatorio, 2-100 caracteres, único sin distinguir mayúsculas |
| `slug` | Opcional; minúsculas, sin acentos, solo `a-z`, `0-9` y guiones; único; en `PUT` si se omite conserva el actual |
| `descripcion` | Opcional, máximo 2000 caracteres |
| `estado` | Solo `activo` o `inactivo`; obligatorio en `PUT` |
| `imagen_portada_url` | Opcional, URL válida `http` o `https`, máximo 500 caracteres |
| `producto_ids` | Opcional en `POST`; obligatorio en `PUT`; máximo 200, sin duplicados, todos deben existir y no estar eliminados |
| Borrado | No eliminar productos; solo las relaciones con la colección |

---

## 7. Formato de errores

Todos los errores usan la misma estructura:

```json
{
  "error": {
    "codigo": "CODIGO_DE_ERROR",
    "mensaje": "Descripción legible para el cliente.",
    "detalles": [
      {
        "campo": "nombre_del_campo",
        "mensaje": "Descripción del problema."
      }
    ]
  }
}
```

`detalles` puede ser un arreglo vacío cuando no aplique.

### 7.1 Error de validación (422)

```json
{
  "error": {
    "codigo": "VALIDACION_FALLIDA",
    "mensaje": "Los datos enviados no son válidos.",
    "detalles": [
      {
        "campo": "precio",
        "mensaje": "El precio debe ser mayor que 0."
      },
      {
        "campo": "sku",
        "mensaje": "El SKU es obligatorio."
      }
    ]
  }
}
```

### 7.2 Recurso no encontrado (404)

```json
{
  "error": {
    "codigo": "RECURSO_NO_ENCONTRADO",
    "mensaje": "No existe un producto con id 999.",
    "detalles": []
  }
}
```

### 7.3 Conflicto de unicidad (409)

```json
{
  "error": {
    "codigo": "CONFLICTO_UNICIDAD",
    "mensaje": "Ya existe un producto con el SKU indicado.",
    "detalles": [
      {
        "campo": "sku",
        "mensaje": "El SKU 'BAG-TOT-001' ya está registrado."
      }
    ]
  }
}
```

### 7.4 Conflicto de dependencias (409)

```json
{
  "error": {
    "codigo": "CONFLICTO_DEPENDENCIAS",
    "mensaje": "No se puede eliminar la categoría porque tiene productos asociados.",
    "detalles": []
  }
}
```

### 7.5 Solicitud inválida (400)

```json
{
  "error": {
    "codigo": "SOLICITUD_INVALIDA",
    "mensaje": "No se pueden enviar 'categoria' y 'categoria_id' al mismo tiempo.",
    "detalles": []
  }
}
```

### 7.6 Error interno (500)

```json
{
  "error": {
    "codigo": "ERROR_INTERNO",
    "mensaje": "Ocurrió un error inesperado.",
    "detalles": []
  }
}
```

### 7.7 No autenticado (401)

```http
POST /api/productos
Content-Type: application/json
```

```json
{
  "error": {
    "codigo": "NO_AUTENTICADO",
    "mensaje": "Se requieren credenciales válidas para realizar esta operación.",
    "detalles": []
  }
}
```

### 7.8 Acceso denegado (403)

```json
{
  "error": {
    "codigo": "ACCESO_DENEGADO",
    "mensaje": "Se requiere el rol administrador para realizar esta operación.",
    "detalles": []
  }
}
```

También se usa `403` cuando un visitante solicita `estado=inactivo` o `estado=todos`. Con el rol único actual, el caso de "autenticado sin rol administrador" queda preparado para futuros roles.

### 7.9 Catálogo de códigos

| Código | HTTP | Uso |
|---|---|---|
| `SOLICITUD_INVALIDA` | 400 | Filtros incompatibles o parámetros mal formados |
| `NO_AUTENTICADO` | 401 | Falta autenticación o credenciales inválidas |
| `ACCESO_DENEGADO` | 403 | Autenticado sin rol administrador, o visitante solicitando datos administrativos |
| `RECURSO_NO_ENCONTRADO` | 404 | Recurso inexistente, borrado o inactivo para visitante |
| `CONFLICTO_UNICIDAD` | 409 | SKU, slug o nombre duplicado |
| `CONFLICTO_DEPENDENCIAS` | 409 | Dependencias al desactivar o eliminar |
| `VALIDACION_FALLIDA` | 422 | Errores de campos, incluido intento de cambiar `sku` |
| `ERROR_INTERNO` | 500 | Error no controlado |

---

## 8. Códigos HTTP

| Código | Uso |
|---|---|
| 200 OK | Consulta o actualización exitosa |
| 201 Created | Recurso creado; incluye cabecera `Location` |
| 204 No Content | Eliminación exitosa, sin cuerpo |
| 400 Bad Request | Filtros incompatibles o parámetros mal formados |
| 401 Unauthorized | Falta autenticación o credenciales inválidas |
| 403 Forbidden | Autenticado sin rol administrador, o solicitud pública de datos administrativos |
| 404 Not Found | Recurso inexistente, borrado o inactivo para visitante |
| 409 Conflict | Duplicado de SKU, slug o nombre; dependencias al desactivar o eliminar |
| 422 Unprocessable Entity | Errores de validación de campos |
| 500 Internal Server Error | Error no controlado |

Notas:

- El orden de validación es autenticación, autorización, validación de datos y existencia del recurso.
- Uvicorn/FastAPI devuelve `422` por validación; la implementación deberá normalizar el cuerpo al formato `error` de este contrato.
- Un recurso inactivo se responde como `404` a visitantes para no revelar su existencia.

---

## 9. Validaciones transversales

1. Recortar espacios al inicio y al final de cadenas; rechazar cadenas vacías cuando el campo sea obligatorio.
2. Normalizar slugs: minúsculas, sin acentos, espacios reemplazados por guiones, sin guiones duplicados ni extremos.
3. Rechazar campos desconocidos en el cuerpo (`extra=forbid`) para evitar asignación masiva.
4. `precio` debe ser un número finito, mayor que 0 y con máximo dos decimales.
5. IDs deben ser enteros positivos.
6. Listas de IDs no deben contener duplicados.
7. `pagina` debe ser mayor o igual a 1; `por_pagina` entre 1 y 100.
8. `estado` solo acepta `activo` o `inactivo`.
9. Fechas de respuesta siempre en UTC con formato ISO 8601.
10. No confiar en datos calculados enviados por el cliente (`id`, `disponible`, `creado_en`, `actualizado_en`, `total_productos`).
11. `POST` devuelve `Location` con la ruta del recurso creado.
12. `PUT` exige el cuerpo completo. En productos, `estado` e `imagenes` son obligatorios; en categorías y colecciones, `estado` es obligatorio. `sku` es inmutable y `slug` se conserva si se omite.
13. `sku` se normaliza a mayúsculas y es único sin distinguir mayúsculas.
14. Las escrituras requieren autenticación y rol `administrador`; las lecturas públicas solo devuelven recursos activos.
15. Un visitante no puede solicitar `estado=inactivo` ni `estado=todos`.
16. Ocultar opciones en el frontend no sustituye la validación de permisos en el backend.
17. CORS no es autorización.

---

## 10. Decisiones pendientes del responsable de Base de Datos

Las siguientes decisiones afectan el contrato y deben aprobarse antes de crear tablas o modelos:

1. **Tipo de PK:** entero autoincremental o UUID.
2. **Precio:** `NUMERIC(10,2)`, entero en centavos u otro; moneda fija (MXN) o campo `moneda`.
3. **Imágenes:** tabla hija, columna JSON o URLs en tabla separada; soporte de subida de archivos.
4. **Relación producto-colección:** tabla puente, claves y si el orden de los productos dentro de la colección es relevante.
5. **Borrado de productos:** implementación del borrado lógico (`eliminado_en`) y exclusión de listados.
6. **Borrado de categorías y colecciones:** borrado físico y comportamiento de claves foráneas.
7. **Unicidad con borrado lógico:** SKU y slug permanecen reservados después de eliminar un producto.
8. **Categorías:** jerarquía con `categoria_padre_id` o categorías planas.
9. **Longitudes y unicidad:** límites definitivos de `nombre`, `descripcion`, `sku` y `slug`; restricciones `UNIQUE`.
10. **Índices:** categoría, estado, existencias, slug, nombre y búsqueda parcial.
11. **Timestamps:** tipo (`timestamp`/`timestamptz`), zona horaria y valores por defecto.
12. **Inventario:** un `existencias` por producto o por variante (variantes fuera de alcance).
13. **Estado:** solo `activo`/`inactivo` o agregar `borrador`/`archivado`.
14. **Slug:** si se genera en la aplicación o en la base de datos, y cómo se resuelven colisiones.
15. **SKU inmutable:** si se refuerza en la base de datos, en la aplicación o en ambos.
16. **Desactivación de categoría:** validar en la aplicación que no tenga productos activos.
17. **Borrado de colección:** eliminar relaciones y conservar productos.

---

## 11. Información requerida del responsable de Frontend

1. Slugs definitivos de las categorías Tote Bags, Cross Body y Mini Bags.
2. Confirmar que "Todas las bolsas" lista todos los productos activos sin filtro.
3. Confirmar si "La Colección" será una sola colección o varias, y su slug definitivo.
4. Si el detalle de producto navegará por `id` o por `slug`.
5. Filtros y ordenamientos que la interfaz mostrará realmente.
6. Paginación por páginas o scroll infinito; tamaño de página esperado.
7. Formato y proporción de imágenes; confirmar si se usarán URLs externas.
8. Moneda y formato de precio (por ejemplo, `$899.00 MXN`).
9. Confirmar que el catálogo público solo mostrará recursos activos.
10. Cómo manejará el frontend `401` y `403` (redirección a inicio de sesión, mensaje, etc.).
11. Mecanismo de inicio de sesión y almacenamiento del token para el panel administrador.
12. Campos adicionales que la interfaz necesite (material, color, medidas, etc.).
13. Estructura de errores que el frontend ya maneja.
14. Ubicación o repositorio del frontend y orígenes CORS definitivos.
15. Confirmar que el detalle de colección consumirá `GET /api/productos?coleccion=...` en lugar de productos embebidos.

---

## 12. Compatibilidad y consideraciones

- Se mantiene el prefijo `/api` y las rutas en español para no romper el frontend existente.
- CORS actual permite `http://localhost:3000` y `http://localhost:5173`; los orígenes definitivos deben confirmarse.
- Los listados públicos devuelven solo `estado=activo` por defecto.
- Los visitantes reciben `404` al solicitar por ID un recurso inactivo.
- Un visitante que solicite `estado=inactivo` o `estado=todos` recibe `403`.
- Los productos agotados siguen visibles si están activos; `disponible=false` permite al frontend mostrarlos como agotados.
- "La Colección" se consume con `GET /api/colecciones/{id}` y sus productos con `GET /api/productos?coleccion=la-coleccion`.
- Las escrituras requieren autenticación y rol `administrador`; el mecanismo se implementará en una fase posterior.
- Ocultar opciones en el frontend no sustituye la validación de permisos en el backend.
- CORS no es un mecanismo de autorización.
- El borrado de productos es lógico; el de categorías y colecciones es físico con validación de dependencias.
- Esta fase no incluye conexión a PostgreSQL, modelos, migraciones ni implementación de endpoints.

---

## 13. Fuera de alcance

- Implementación de autenticación y autorización.
- Carrito de compras.
- Órdenes y pagos.
- Subida de archivos de imagen.
- Variantes de producto (color, talla).
- Inventario por sucursal.
- Reseñas, descuentos y cupones.
- Conexión a base de datos y migraciones.
- Implementación de routers, servicios o modelos.
