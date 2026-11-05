# BagStore — Propuesta de contrato de API v0.3.0

**Versión propuesta:** 0.3.0
**Contrato base:** `docs/api-contract.md` v0.2.0 (borrador)
**Estado:** propuesta para revisión. No reemplaza el contrato actual.
**Base URL de desarrollo:** `http://localhost:8000`
**Prefijo:** `/api`
**Formato:** JSON UTF-8
**Autenticación:** propuesta, pendiente de aprobación
**Roles propuestos:** `cliente`, `administrador`

> Este documento conserva los endpoints existentes de la versión 0.2.0. Las nuevas funcionalidades se incorporan mediante rutas adicionales o mediante ampliaciones compatibles que requieren aprobación explícita.

---

## Tabla de contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Diagnóstico del contrato actual](#2-diagnóstico-del-contrato-actual)
3. [Matriz de requerimientos](#3-matriz-de-requerimientos)
4. [Actores y control de acceso](#4-actores-y-control-de-acceso)
5. [Convenciones](#5-convenciones)
6. [Resumen de endpoints](#6-resumen-de-endpoints)
7. [Autenticación y sesiones](#7-autenticación-y-sesiones)
8. [Catálogo existente](#8-catálogo-existente)
9. [Colores](#9-colores)
10. [Imágenes y fotografías](#10-imágenes-y-fotografías)
11. [Colecciones administrativas](#11-colecciones-administrativas)
12. [Inventario](#12-inventario)
13. [Pedidos](#13-pedidos)
14. [Idempotencia y concurrencia](#14-idempotencia-y-concurrencia)
15. [Pagos](#15-pagos)
16. [Envíos, paqueterías y tarifas](#16-envíos-paqueterías-y-tarifas)
17. [Reportes y tickets](#17-reportes-y-tickets)
18. [Reseñas](#18-reseñas)
19. [Devoluciones, reembolsos y reposición](#19-devoluciones-reembolsos-y-reposición)
20. [Formato de errores](#20-formato-de-errores)
21. [Códigos HTTP](#21-códigos-http)
22. [Validaciones transversales](#22-validaciones-transversales)
23. [Entidades y relaciones para PostgreSQL](#23-entidades-y-relaciones-para-postgresql)
24. [Transacciones, bloqueo e idempotencia](#24-transacciones-bloqueo-e-idempotencia)
25. [Decisiones pendientes](#25-decisiones-pendientes)
26. [Compatibilidad con 0.2.0](#26-compatibilidad-con-020)
27. [Fuera de alcance](#27-fuera-de-alcance)
28. [Checklist de aprobación](#28-checklist-de-aprobación)

---

## 1. Resumen ejecutivo

La versión 0.2.0 documenta únicamente el módulo de catálogo. La propuesta 0.3.0 amplía el contrato para cubrir:

- Persistencia en PostgreSQL.
- Registro, login, logout y sesión activa.
- Roles `cliente` y `administrador`.
- Protección de rutas administrativas.
- Catálogo de colores y filtros.
- Subida de imágenes con URL permanente.
- Consulta administrativa de colecciones.
- Inventario con historial.
- Pedidos, pagos, envíos, reportes, reseñas y devoluciones.
- Idempotencia y control de concurrencia.
- Errores uniformes ampliados.

La propuesta mantiene los endpoints actuales y evita cambiar sus respuestas públicas. Las nuevas capacidades se exponen mediante rutas nuevas, principalmente bajo `/api/admin`.

---

## 2. Diagnóstico del contrato actual

### 2.1 Contrato existente

`docs/api-contract.md` se identifica ya como **v0.2.0 (borrador)**, aunque su estado indica “Sin implementación”. El backend actual sí implementa:

- `GET /api/health`.
- CRUD de productos.
- CRUD de categorías.
- CRUD de colecciones.
- Filtros, ordenamiento, paginación y borrado lógico de productos.
- Validaciones Pydantic.
- Errores uniformes.
- Repositorios en memoria.
- Pruebas automatizadas y documentación Swagger.

### 2.2 Diferencias entre contrato y realidad

| Aspecto | Contrato actual | Implementación actual |
|---|---|---|
| Persistencia | PostgreSQL pendiente | Memoria temporal |
| Autenticación | Diseñada, no implementada | Dependencia no-op |
| Roles | Solo administrador previsto | Sin autenticación real |
| Imágenes | URLs manuales | URLs manuales, sin subida |
| Existencias | Edición manual | `existencias` editable en producto |
| Colecciones | Sin productos embebidos | Sin productos embebidos |
| Pedidos, pagos, envíos | Fuera de alcance | No implementados |
| Reseñas, devoluciones | Fuera de alcance | No implementadas |

### 2.3 Decisión de versión

El contrato actual ya ocupa la versión 0.2.0. Para evitar dos documentos con la misma versión, esta ampliación se propone como **0.3.0**. Si el equipo exige que la ampliación sea 0.2.0, primero debe corregirse formalmente la versión del contrato base.

---

## 3. Matriz de requerimientos

| # | Requerimiento | Estado actual | Tipo | Acción propuesta |
|---|---|---|---|---|
| 1 | PostgreSQL y persistencia permanente | Memoria temporal | Nuevo | Definir entidades, migraciones y capa de persistencia |
| 2 | Registro, login, logout y sesión | No existe | Nuevo | Módulo `/api/auth` |
| 3 | Roles cliente y administrador | Solo administrador previsto | Ampliación | Añadir rol `cliente` y autorización |
| 4 | Protección administrativa | No implementada | Ampliación | Autenticación y autorización por rol |
| 5 | Colores, duplicados y filtros | No existe | Nuevo | CRUD de colores y relación con productos |
| 6 | Subida de fotografías | Solo URL manual | Ampliación | Subida multipart y URL permanente |
| 7 | Colecciones admin con productos activos/inactivos | No existe | Nuevo | Rutas `/api/admin/colecciones` |
| 8 | Inventario con ajustes, motivos e historial | `existencias` manual | Ampliación/Nuevo | Movimientos de inventario y stock controlado |
| 9 | Validación y descuento seguro de existencias | No existe | Nuevo | Transacciones y bloqueo |
| 10 | Pedidos con datos históricos | No existe | Nuevo | Módulo `/api/pedidos` |
| 11 | Prevención de duplicados y compras simultáneas | No existe | Nuevo | Idempotencia y bloqueo |
| 12 | Entrega, destinatario, domicilio, teléfono y tarifas | No existe | Nuevo | Datos de envío y tarifas |
| 13 | Registro y verificación de pagos | No existe | Nuevo | Módulo de pagos |
| 14 | Envíos, paqueterías, guías y seguimiento | No existe | Nuevo | Módulo de envíos |
| 15 | Reportes de ventas y tickets | No existe | Nuevo | Rutas administrativas de reportes |
| 16 | Reseñas y comentarios | No existe | Nuevo | Módulo de reseñas |
| 17 | Devoluciones, reembolsos y reposición | No existe | Nuevo | Módulo de devoluciones |
| 18 | CORS y errores uniformes | Parcial | Ampliación | Extender catálogo de errores y configuración |

---

## 4. Actores y control de acceso

| Actor | Permisos |
|---|---|
| Visitante | Consulta de catálogo activo, colores, reseñas públicas, cotización de envío |
| Cliente | Todo lo del visitante, más su sesión, sus pedidos, sus pagos, sus reseñas y sus devoluciones |
| Administrador | Acceso completo, incluyendo recursos inactivos, inventario, pedidos, pagos, envíos, reportes y moderación |

Reglas propuestas:

- Las escrituras de catálogo, colores, inventario, pedidos administrativos, pagos, envíos, reportes y reseñas administrativas requieren rol `administrador`.
- El cliente solo puede consultar y modificar sus propios recursos.
- Un recurso de otro cliente debe devolver `404` para no revelar su existencia.
- La autenticación se implementará con el mecanismo que apruebe el equipo.
- Ocultar botones en el frontend no sustituye la autorización del backend.
- CORS no es un mecanismo de autorización.

---

## 5. Convenciones

| Convención | Definición |
|---|---|
| Nombres de campos | `snake_case` en español |
| Rutas | Sustantivos plurales y español |
| Prefijo | `/api` |
| Versionado de ruta | Sin `/v1` en esta propuesta, pendiente de decisión |
| IDs | Enteros positivos; UUID pendiente de decisión de BD |
| Fechas | ISO 8601 en UTC, con sufijo `Z` |
| Dinero | Decimal en JSON; precisión y moneda pendientes de BD |
| Listados | Envoltura `datos` + `paginacion` |
| Errores | Envoltura única `error` |
| `PUT` | Reemplazo completo |
| `PATCH` | No incluido salvo decisión expresa |
| Borrado | Depende de la entidad; se documenta por módulo |
| Idempotencia | Cabecera `Idempotency-Key` propuesta para operaciones críticas |
| Concurrencia | Transacciones y bloqueo de filas en PostgreSQL |

### 5.1 Idempotencia propuesta

Cabecera:

```http
Idempotency-Key: 7f1c7e9a-8a4c-4e5f-9b1a-3c2d1e0f9a8b
```

Reglas propuestas:

- Obligatoria en `POST /api/pedidos`.
- Recomendada en creación de pagos, devoluciones y reembolsos.
- La misma clave con el mismo cuerpo devuelve la misma respuesta.
- La misma clave con un cuerpo distinto devuelve `409`.
- La clave se asocia al usuario autenticado.
- La persistencia y el tiempo de expiración quedan pendientes de aprobación.

### 5.2 CORS

La configuración de CORS debe seguir siendo explícita y configurable por entorno:

- Orígenes permitidos definidos en variables de entorno.
- Métodos permitidos explícitos: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`.
- Cabeceras permitidas explícitas, incluyendo `Authorization`, `Content-Type` e `Idempotency-Key`.
- `allow_credentials` solo con orígenes explícitos, nunca con `*`.
- Los orígenes definitivos del frontend deben ser aprobados.
- CORS no sustituye la autenticación ni la autorización.

---

## 6. Resumen de endpoints

### 6.1 Existentes sin cambios

```text
GET    /api/health

GET    /api/productos
GET    /api/productos/{id}
POST   /api/productos
PUT    /api/productos/{id}
DELETE /api/productos/{id}

GET    /api/categorias
GET    /api/categorias/{id}
POST   /api/categorias
PUT    /api/categorias/{id}
DELETE /api/categorias/{id}

GET    /api/colecciones
GET    /api/colecciones/{id}
POST   /api/colecciones
PUT    /api/colecciones/{id}
DELETE /api/colecciones/{id}
```

### 6.2 Autenticación

```text
POST   /api/auth/registro
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/sesion
```

### 6.3 Colores

```text
GET    /api/colores
GET    /api/colores/{id}
POST   /api/colores
PUT    /api/colores/{id}
DELETE /api/colores/{id}

GET    /api/colores/{id}/productos
GET    /api/productos/{id}/colores
PUT    /api/productos/{id}/colores
```

### 6.4 Imágenes

```text
POST   /api/productos/{id}/imagenes
PUT    /api/productos/{id}/imagenes/{imagen_id}
DELETE /api/productos/{id}/imagenes/{imagen_id}
```

### 6.5 Colecciones administrativas

```text
GET    /api/admin/colecciones
GET    /api/admin/colecciones/{id}
GET    /api/admin/colecciones/{id}/productos
```

### 6.6 Inventario

```text
GET    /api/admin/productos/{id}/inventario
POST   /api/admin/productos/{id}/inventario/ajustes
GET    /api/admin/productos/{id}/inventario/historial
```

### 6.7 Pedidos

```text
POST   /api/pedidos
GET    /api/pedidos
GET    /api/pedidos/{id}

GET    /api/admin/pedidos
GET    /api/admin/pedidos/{id}
PUT    /api/admin/pedidos/{id}/estado
GET    /api/admin/pedidos/{id}/ticket
```

### 6.8 Pagos

```text
POST   /api/pedidos/{id}/pagos
GET    /api/pedidos/{id}/pagos
GET    /api/admin/pagos
GET    /api/admin/pagos/{id}
PUT    /api/admin/pagos/{id}/estado
POST   /api/pagos/webhook
```

### 6.9 Envíos

```text
POST   /api/envios/cotizar
GET    /api/pedidos/{id}/envio

GET    /api/admin/paqueterias
POST   /api/admin/paqueterias
GET    /api/admin/paqueterias/{id}
PUT    /api/admin/paqueterias/{id}
DELETE /api/admin/paqueterias/{id}

GET    /api/admin/tarifas-envio
POST   /api/admin/tarifas-envio
GET    /api/admin/tarifas-envio/{id}
PUT    /api/admin/tarifas-envio/{id}
DELETE /api/admin/tarifas-envio/{id}

GET    /api/admin/envios
GET    /api/admin/envios/{id}
PUT    /api/admin/envios/{id}
```

### 6.10 Reportes

```text
GET    /api/admin/reportes/ventas
GET    /api/admin/reportes/productos
```

### 6.11 Reseñas

```text
GET    /api/productos/{id}/resenas
POST   /api/productos/{id}/resenas

GET    /api/admin/resenas
GET    /api/admin/resenas/{id}
PUT    /api/admin/resenas/{id}
DELETE /api/admin/resenas/{id}
```

### 6.12 Devoluciones y reembolsos

```text
POST   /api/pedidos/{id}/devoluciones
GET    /api/pedidos/{id}/devoluciones

GET    /api/admin/devoluciones
GET    /api/admin/devoluciones/{id}
PUT    /api/admin/devoluciones/{id}/estado
POST   /api/admin/devoluciones/{id}/reembolsos
GET    /api/admin/reembolsos/{id}
PUT    /api/admin/reembolsos/{id}/estado
```

---

## 7. Autenticación y sesiones

### 7.1 Registro

```http
POST /api/auth/registro
Content-Type: application/json
```

```json
{
  "nombre": "Ana Pérez",
  "email": "ana@example.com",
  "password": "una-contraseña-segura",
  "telefono": "+5215512345678"
}
```

Respuesta `201 Created`:

```json
{
  "id": 15,
  "nombre": "Ana Pérez",
  "email": "ana@example.com",
  "telefono": "+5215512345678",
  "rol": "cliente",
  "estado": "activo",
  "creado_en": "2026-11-04T18:00:00Z"
}
```

Reglas propuestas:

- El registro público siempre crea rol `cliente`.
- El email es único sin distinguir mayúsculas.
- La contraseña nunca se devuelve.
- La verificación de correo queda pendiente.
- La creación del primer administrador queda pendiente.

### 7.2 Login

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "ana@example.com",
  "password": "una-contraseña-segura"
}
```

Respuesta `200 OK`:

```json
{
  "access_token": "token-de-acceso",
  "token_type": "bearer",
  "expira_en": 3600,
  "usuario": {
    "id": 15,
    "nombre": "Ana Pérez",
    "email": "ana@example.com",
    "rol": "cliente"
  }
}
```

La forma exacta del token depende de la decisión entre JWT, cookies o sesiones opacas.

### 7.3 Sesión activa

```http
GET /api/auth/sesion
Authorization: Bearer <token>
```

```json
{
  "autenticado": true,
  "usuario": {
    "id": 15,
    "nombre": "Ana Pérez",
    "email": "ana@example.com",
    "rol": "cliente"
  },
  "expira_en": "2026-11-04T19:00:00Z"
}
```

### 7.4 Logout

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

Respuesta `204 No Content`.

Reglas propuestas:

- Si se usan sesiones opacas, el token se revoca en servidor.
- Si se usan JWT sin estado, debe definirse una lista de revocación o tokens de corta duración.
- Logout debe ser idempotente.

### 7.5 Errores de autenticación

| Caso | HTTP | Código propuesto |
|---|---:|---|
| Credenciales inválidas | 401 | `NO_AUTENTICADO` o `CREDENCIALES_INVALIDAS` |
| Sesión expirada | 401 | `SESION_EXPIRADA` |
| Sin rol administrador | 403 | `ACCESO_DENEGADO` |
| Usuario inactivo | 403 | `ACCESO_DENEGADO` |
| Email duplicado | 409 | `CONFLICTO_UNICIDAD` |

La creación de `CREDENCIALES_INVALIDAS` y `SESION_EXPIRADA` requiere aprobación para no duplicar `NO_AUTENTICADO`.

---

## 8. Catálogo existente

Los módulos de productos, categorías y colecciones mantienen sus endpoints y estructuras de 0.2.0.

Reglas que se conservan:

- Lecturas públicas solo de recursos activos.
- Escrituras administrativas.
- Productos agotados visibles si están activos.
- Productos inactivos no visibles públicamente.
- Borrado lógico de productos.
- Borrado físico de categorías y colecciones con validación de dependencias.
- Colecciones administradas desde `producto_ids`.
- Respuesta de colección sin productos embebidos.

### 8.1 Ampliaciones compatibles pendientes de aprobación

- Añadir colores a productos mediante subrecursos, sin cambiar la respuesta actual.
- Añadir filtros de color mediante `/api/colores/{id}/productos` o, alternativamente, parámetros opcionales en `GET /api/productos`.
- Exponer imágenes subidas dentro del arreglo `imagenes` del producto.
- Añadir nuevos estados o campos de inventario sin romper `existencias`.

---

## 9. Colores

### 9.1 Campos propuestos

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | entero | Respuesta | Positivo, inmutable |
| `nombre` | string | Sí | 2 a 50 caracteres, único sin distinguir mayúsculas |
| `slug` | string | No | Generado desde nombre, único |
| `codigo_hex` | string | No | Formato `#RRGGBB`, si se aprueba |
| `estado` | enum | No en POST | `activo`/`inactivo`, por defecto `activo` |
| `creado_en` | datetime | Respuesta | UTC |
| `actualizado_en` | datetime | Respuesta | UTC |

### 9.2 Endpoints

```text
GET    /api/colores
GET    /api/colores/{id}
POST   /api/colores
PUT    /api/colores/{id}
DELETE /api/colores/{id}
GET    /api/colores/{id}/productos
GET    /api/productos/{id}/colores
PUT    /api/productos/{id}/colores
```

### 9.3 Crear color

```http
POST /api/colores
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "nombre": "Verde oliva",
  "slug": "verde-oliva",
  "codigo_hex": "#556B2F",
  "estado": "activo"
}
```

Respuesta `201 Created`:

```json
{
  "id": 4,
  "nombre": "Verde oliva",
  "slug": "verde-oliva",
  "codigo_hex": "#556B2F",
  "estado": "activo",
  "creado_en": "2026-11-04T18:00:00Z",
  "actualizado_en": "2026-11-04T18:00:00Z"
}
```

### 9.4 Productos por color

```http
GET /api/colores/4/productos?pagina=1&por_pagina=20&orden=reciente
```

Respuesta con la misma envoltura de productos:

```json
{
  "datos": [
    {
      "id": 12,
      "nombre": "Tote Bag Aurora",
      "slug": "tote-bag-aurora",
      "precio": 899.0,
      "disponible": true,
      "estado": "activo",
      "imagen_principal": null,
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

### 9.5 Colores de un producto

```http
GET /api/productos/12/colores
```

```json
{
  "datos": [
    {
      "id": 4,
      "nombre": "Verde oliva",
      "slug": "verde-oliva",
      "codigo_hex": "#556B2F",
      "estado": "activo"
    }
  ]
}
```

Reemplazo administrativo:

```http
PUT /api/productos/12/colores
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "color_ids": [1, 4]
}
```

### 9.6 Decisiones pendientes de colores

- Un color por producto o varios colores por producto.
- Si el color forma parte del SKU o de una variante de producto.
- Si el color tiene código hexadecimal.
- Si el color puede desactivarse y qué ocurre con productos activos.
- Si se permiten colores duplicados por nombre o slug.
- Si el frontend requiere filtros combinados de color, categoría y colección.

---

## 10. Imágenes y fotografías

### 10.1 Campos propuestos

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | entero | Respuesta | Positivo |
| `producto_id` | entero | Respuesta | Producto asociado |
| `url` | string | Respuesta | URL permanente `http` o `https` |
| `texto_alternativo` | string | No | Máximo 150 caracteres |
| `orden` | entero | No | Mayor o igual a 0, sin duplicados por producto |
| `es_principal` | booleano | No | Máximo una principal por producto |
| `creado_en` | datetime | Respuesta | UTC |
| `actualizado_en` | datetime | Respuesta | UTC |

### 10.2 Subir imagen

```http
POST /api/productos/12/imagenes
Authorization: Bearer <token-admin>
Content-Type: multipart/form-data
```

Campos:

- `archivo`: archivo de imagen.
- `texto_alternativo`: opcional.
- `orden`: opcional.
- `es_principal`: opcional.

Respuesta `201 Created`:

```json
{
  "id": 31,
  "producto_id": 12,
  "url": "https://cdn.bagstore.com/productos/12/31.jpg",
  "texto_alternativo": "Tote Bag Aurora vista frontal",
  "orden": 1,
  "es_principal": true,
  "creado_en": "2026-11-04T18:00:00Z"
}
```

### 10.3 Actualizar metadatos

```http
PUT /api/productos/12/imagenes/31
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "texto_alternativo": "Tote Bag Aurora vista lateral",
  "orden": 2,
  "es_principal": false
}
```

### 10.4 Eliminar imagen

```http
DELETE /api/productos/12/imagenes/31
Authorization: Bearer <token-admin>
```

Respuesta `204 No Content`.

### 10.5 Reglas propuestas

- La URL debe ser permanente.
- El almacenamiento puede ser local o externo.
- Debe definirse tamaño máximo, tipos MIME permitidos y dimensiones.
- Si se marca una imagen como principal, las demás deben dejar de serlo.
- Si no se marca ninguna, la primera por orden será la principal.
- El producto puede seguir aceptando URLs manuales por compatibilidad.
- Debe existir una estrategia de limpieza de archivos huérfanos.
- La subida debe validar el archivo y no confiar en la extensión.

### 10.6 Decisiones pendientes de imágenes

- Almacenamiento local, S3 u otro servicio.
- Tamaño máximo y tipos permitidos.
- Si se permite eliminar imágenes usadas por pedidos históricos.
- Si el producto debe guardar `imagen_id` o solo `url`.
- Si se permite reordenar imágenes en una sola llamada.
- Si las imágenes se sirven desde el mismo dominio o desde un CDN.

---

## 11. Colecciones administrativas

### 11.1 Listar colecciones administrativas

```http
GET /api/admin/colecciones?estado=todos&pagina=1&por_pagina=20
Authorization: Bearer <token-admin>
```

```json
{
  "datos": [
    {
      "id": 2,
      "nombre": "Archivo",
      "slug": "archivo",
      "descripcion": "Colección histórica.",
      "estado": "inactivo",
      "imagen_portada_url": "https://cdn.bagstore.com/colecciones/archivo.jpg",
      "total_productos": 12,
      "creado_en": "2026-11-01T09:00:00Z",
      "actualizado_en": "2026-11-01T09:00:00Z"
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

### 11.2 Productos de una colección

```http
GET /api/admin/colecciones/2/productos?estado=todos&pagina=1&por_pagina=20&orden=reciente
Authorization: Bearer <token-admin>
```

```json
{
  "datos": [
    {
      "id": 4,
      "nombre": "Cross Body Noche",
      "slug": "cross-body-noche",
      "precio": 1199.0,
      "disponible": true,
      "estado": "inactivo",
      "imagen_principal": {
        "url": "https://cdn.bagstore.com/productos/cross-noche-1.jpg",
        "texto_alternativo": "Cross Body Noche",
        "orden": 1,
        "es_principal": true
      },
      "categoria": {
        "id": 1,
        "nombre": "Cross Body",
        "slug": "cross-body"
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

Reglas propuestas:

- `estado` acepta `activo`, `inactivo` o `todos`.
- Solo administradores pueden usar `inactivo` y `todos`.
- Los productos eliminados lógicamente no se incluyen.
- La respuesta reutiliza `ProductoResumen`.

---

## 12. Inventario

### 12.1 Consultar inventario

```http
GET /api/admin/productos/12/inventario
Authorization: Bearer <token-admin>
```

```json
{
  "producto_id": 12,
  "sku": "BAG-TOT-001",
  "existencias": 12,
  "disponible": true,
  "actualizado_en": "2026-11-04T18:00:00Z"
}
```

### 12.2 Ajustar inventario

```http
POST /api/admin/productos/12/inventario/ajustes
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "tipo": "entrada",
  "cantidad": 5,
  "motivo": "reposicion_proveedor",
  "referencia": "OC-2026-001",
  "nota": "Reposición de temporada"
}
```

Respuesta `201 Created`:

```json
{
  "id": 101,
  "producto_id": 12,
  "tipo": "entrada",
  "cantidad": 5,
  "stock_anterior": 12,
  "stock_nuevo": 17,
  "motivo": "reposicion_proveedor",
  "referencia": "OC-2026-001",
  "nota": "Reposición de temporada",
  "usuario_id": 1,
  "creado_en": "2026-11-04T18:00:00Z"
}
```

### 12.3 Historial

```http
GET /api/admin/productos/12/inventario/historial?pagina=1&por_pagina=20
Authorization: Bearer <token-admin>
```

```json
{
  "datos": [
    {
      "id": 101,
      "tipo": "entrada",
      "cantidad": 5,
      "stock_anterior": 12,
      "stock_nuevo": 17,
      "motivo": "reposicion_proveedor",
      "referencia": "OC-2026-001",
      "usuario_id": 1,
      "creado_en": "2026-11-04T18:00:00Z"
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

### 12.4 Semántica propuesta de ajustes

| Tipo | Significado |
|---|---|
| `entrada` | Suma `cantidad` al stock |
| `salida` | Resta `cantidad` al stock |
| `ajuste` | Establece el stock final en `cantidad` |

Alternativas pendientes:

- Usar `cantidad_delta` firmado para todos los tipos.
- Separar `entrada`, `salida` y `ajuste_absoluto` en endpoints distintos.
- Permitir stock negativo o bloquearlo.

### 12.5 Decisiones pendientes de inventario

- Si `existencias` en producto es la fuente de verdad o un valor derivado.
- Si el inventario se descuenta al crear el pedido, al confirmar el pago o al reservar.
- Si las reservas vencen.
- Si se permite sobreventa o backorder.
- Si el ajuste manual de `existencias` en producto se mantiene por compatibilidad.
- Quién puede ajustar inventario y con qué motivo.
- Si el historial es inmutable.
- Si se requiere inventario por variante/color/talla.

---

## 13. Pedidos

### 13.1 Crear pedido

```http
POST /api/pedidos
Authorization: Bearer <token-cliente>
Idempotency-Key: 7f1c7e9a-8a4c-4e5f-9b1a-3c2d1e0f9a8b
Content-Type: application/json
```

```json
{
  "items": [
    {
      "producto_id": 12,
      "cantidad": 2
    },
    {
      "producto_id": 18,
      "cantidad": 1
    }
  ],
  "entrega": {
    "destinatario": "Ana Pérez",
    "telefono": "+5215512345678",
    "calle": "Av. Reforma",
    "numero": "123",
    "interior": "4B",
    "colonia": "Centro",
    "ciudad": "Ciudad de México",
    "estado": "CDMX",
    "pais": "México",
    "codigo_postal": "06000",
    "referencias": "Edificio azul"
  },
  "envio": {
    "paqueteria_id": 1,
    "tarifa_id": 3
  },
  "metodo_pago": "pendiente",
  "notas": "Entregar por la tarde"
}
```

Respuesta `201 Created`:

```json
{
  "id": 501,
  "numero": "BS-2026-000501",
  "cliente_id": 15,
  "estado": "pendiente_pago",
  "items": [
    {
      "id": 9001,
      "producto_id": 12,
      "sku": "BAG-TOT-001",
      "nombre": "Tote Bag Aurora",
      "cantidad": 2,
      "precio_unitario": 899.0,
      "descuento_unitario": 0.0,
      "subtotal": 1798.0
    }
  ],
  "subtotal": 1798.0,
  "descuento_total": 0.0,
  "envio_total": 150.0,
  "total": 1948.0,
  "moneda": "MXN",
  "entrega": {
    "destinatario": "Ana Pérez",
    "telefono": "+5215512345678",
    "calle": "Av. Reforma",
    "numero": "123",
    "interior": "4B",
    "colonia": "Centro",
    "ciudad": "Ciudad de México",
    "estado": "CDMX",
    "pais": "México",
    "codigo_postal": "06000",
    "referencias": "Edificio azul"
  },
  "creado_en": "2026-11-04T18:00:00Z",
  "actualizado_en": "2026-11-04T18:00:00Z"
}
```

Reglas propuestas:

- El cliente no envía precios ni totales.
- El servidor calcula precios, descuentos, envío y total.
- Los items guardan una copia histórica del producto.
- Si el producto cambia después, el pedido conserva el nombre, SKU y precio original.
- El pedido debe crearse en una transacción.
- La clave de idempotencia evita pedidos duplicados.

### 13.2 Listar pedidos propios

```http
GET /api/pedidos?pagina=1&por_pagina=20&estado=pendiente_pago
Authorization: Bearer <token-cliente>
```

```json
{
  "datos": [
    {
      "id": 501,
      "numero": "BS-2026-000501",
      "estado": "pendiente_pago",
      "total": 1948.0,
      "moneda": "MXN",
      "creado_en": "2026-11-04T18:00:00Z"
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

### 13.3 Detalle de pedido

```http
GET /api/pedidos/501
Authorization: Bearer <token-cliente>
```

Devuelve el pedido completo, sus items históricos, pagos, envío y devoluciones asociadas, según permisos.

### 13.4 Pedidos administrativos

```http
GET /api/admin/pedidos?estado=pagado&desde=2026-11-01&hasta=2026-11-30&pagina=1&por_pagina=20
Authorization: Bearer <token-admin>
```

### 13.5 Cambiar estado

```http
PUT /api/admin/pedidos/501/estado
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "estado": "en_preparacion",
  "motivo": "Pago verificado",
  "nota": "Preparar para envío"
}
```

Respuesta `200 OK` con el pedido actualizado.

### 13.6 Estados propuestos

Los estados son una propuesta y requieren aprobación:

```text
pendiente_pago
pagado
en_preparacion
enviado
entregado
cancelado
devuelto
reembolsado
```

Reglas pendientes:

- Qué transiciones son válidas.
- Quién puede cancelar.
- Si se puede cancelar después del pago.
- Si el estado se deriva de pagos y envíos o se controla manualmente.
- Si se requiere historial de estados.

### 13.7 Ticket

```http
GET /api/admin/pedidos/501/ticket
Authorization: Bearer <token-admin>
```

```json
{
  "pedido_id": 501,
  "numero": "BS-2026-000501",
  "fecha": "2026-11-04T18:00:00Z",
  "cliente": {
    "id": 15,
    "nombre": "Ana Pérez",
    "email": "ana@example.com"
  },
  "items": [
    {
      "sku": "BAG-TOT-001",
      "nombre": "Tote Bag Aurora",
      "cantidad": 2,
      "precio_unitario": 899.0,
      "subtotal": 1798.0
    }
  ],
  "subtotal": 1798.0,
  "descuento_total": 0.0,
  "envio_total": 150.0,
  "total": 1948.0,
  "moneda": "MXN",
  "pago": {
    "estado": "pendiente",
    "metodo": "pendiente"
  },
  "envio": {
    "paqueteria": "Paquetería Demo",
    "guia": null
  }
}
```

---

## 14. Idempotencia y concurrencia

### 14.1 Creación de pedido

Flujo propuesto:

1. Validar autenticación y rol.
2. Validar `Idempotency-Key`.
3. Buscar la clave para el usuario.
4. Si ya existe y el cuerpo coincide, devolver la respuesta anterior.
5. Si ya existe y el cuerpo difiere, devolver `409`.
6. Abrir transacción.
7. Bloquear inventario de los productos solicitados.
8. Validar existencias.
9. Calcular precios, descuentos, envío y total.
10. Crear pedido e items históricos.
11. Descontar o reservar inventario.
12. Registrar movimiento de inventario.
13. Guardar la clave de idempotencia.
14. Confirmar transacción.

Decisiones pendientes:

- Descontar stock al crear, al pagar o al reservar.
- Usar `READ COMMITTED` con `SELECT ... FOR UPDATE` o `SERIALIZABLE`.
- Tiempo de vida de la clave de idempotencia.
- Política de reintentos ante conflictos de serialización.
- Si la respuesta idempotente se guarda completa o solo el ID del pedido.

### 14.2 Concurrencia de inventario

- Bloquear filas de inventario antes de validar.
- Actualizar stock con condición de suficiencia.
- Rechazar con `409 STOCK_INSUFICIENTE` si no alcanza.
- Registrar siempre el movimiento con stock anterior y nuevo.
- No confiar en el stock calculado en el frontend.

### 14.3 Otras operaciones

| Operación | Mecanismo |
|---|---|
| Ajuste de inventario | Transacción + historial |
| Confirmación de pago | Transacción + referencia única |
| Devolución | Transacción + estado condicional |
| Reembolso | Transacción + idempotencia |
| Reposición de stock | Transacción + una sola aplicación por devolución |
| Seguimiento de envío | Idempotencia por evento externo |
| Reseña | Restricción única por producto/cliente/pedido |
| Color | Restricción única por nombre/slug |

---

## 15. Pagos

### 15.1 Campos propuestos

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | entero | Positivo |
| `pedido_id` | entero | Pedido asociado |
| `metodo` | string | Pendiente de catálogo |
| `proveedor` | string | Pasarela o `manual` |
| `referencia_externa` | string | Única si existe |
| `monto` | decimal | Positivo |
| `moneda` | string | Pendiente |
| `estado` | enum | Pendiente de aprobación |
| `verificado_en` | datetime | Opcional |
| `creado_en` | datetime | UTC |
| `actualizado_en` | datetime | UTC |

### 15.2 Registrar pago

```http
POST /api/pedidos/501/pagos
Authorization: Bearer <token-cliente>
Content-Type: application/json
```

```json
{
  "metodo": "transferencia",
  "proveedor": "manual",
  "referencia_externa": "TRX-2026-001"
}
```

Respuesta `201 Created`:

```json
{
  "id": 7001,
  "pedido_id": 501,
  "metodo": "transferencia",
  "proveedor": "manual",
  "referencia_externa": "TRX-2026-001",
  "monto": 1948.0,
  "moneda": "MXN",
  "estado": "pendiente_verificacion",
  "verificado_en": null,
  "creado_en": "2026-11-04T18:10:00Z",
  "actualizado_en": "2026-11-04T18:10:00Z"
}
```

### 15.3 Verificar pago

```http
PUT /api/admin/pagos/7001/estado
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "estado": "verificado",
  "motivo": "Comprobante validado",
  "referencia_externa": "TRX-2026-001"
}
```

### 15.4 Estados propuestos

```text
pendiente
pendiente_verificacion
verificado
rechazado
reembolsado
parcialmente_reembolsado
```

### 15.5 Webhook

```http
POST /api/pagos/webhook
Content-Type: application/json
```

La ruta queda condicionada a la pasarela elegida. Debe validar firma, ser idempotente y no confiar en el cuerpo sin verificación.

### 15.6 Decisiones pendientes de pagos

- Pasarela y métodos de pago.
- Pago manual o verificación automática.
- Estados exactos.
- Pagos parciales.
- Reembolsos parciales.
- Manejo de contracargos.
- Validación de webhooks.
- Moneda y tipo de cambio.

---

## 16. Envíos, paqueterías y tarifas

### 16.1 Cotizar envío

```http
POST /api/envios/cotizar
Content-Type: application/json
```

```json
{
  "codigo_postal": "06000",
  "pais": "México",
  "peso_total_gramos": 1200,
  "subtotal": 1798.0
}
```

Respuesta `200 OK`:

```json
{
  "opciones": [
    {
      "paqueteria_id": 1,
      "paqueteria": "Paquetería Demo",
      "tarifa_id": 3,
      "nombre": "Estándar",
      "costo": 150.0,
      "moneda": "MXN",
      "dias_estimados": 3
    }
  ]
}
```

### 16.2 Paqueterías administrativas

```http
GET /api/admin/paqueterias
Authorization: Bearer <token-admin>
```

```json
{
  "datos": [
    {
      "id": 1,
      "nombre": "Paquetería Demo",
      "slug": "paqueteria-demo",
      "activo": true,
      "url_seguimiento_plantilla": "https://paqueteria.example/tracking/{guia}",
      "creado_en": "2026-11-01T09:00:00Z",
      "actualizado_en": "2026-11-01T09:00:00Z"
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

### 16.3 Tarifas

```http
POST /api/admin/tarifas-envio
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "paqueteria_id": 1,
  "nombre": "Estándar nacional",
  "pais": "México",
  "codigo_postal_desde": "00000",
  "codigo_postal_hasta": "99999",
  "peso_min_gramos": 0,
  "peso_max_gramos": 5000,
  "precio": 150.0,
  "moneda": "MXN",
  "activo": true,
  "vigencia_desde": "2026-11-01",
  "vigencia_hasta": null
}
```

### 16.4 Envío de un pedido

```http
GET /api/pedidos/501/envio
Authorization: Bearer <token-cliente>
```

```json
{
  "id": 801,
  "pedido_id": 501,
  "paqueteria": {
    "id": 1,
    "nombre": "Paquetería Demo",
    "slug": "paqueteria-demo"
  },
  "estado": "en_transito",
  "numero_guia": "DEMO-123456",
  "url_seguimiento": "https://paqueteria.example/tracking/DEMO-123456",
  "costo": 150.0,
  "moneda": "MXN",
  "destinatario": {
    "nombre": "Ana Pérez",
    "telefono": "+5215512345678",
    "calle": "Av. Reforma",
    "numero": "123",
    "interior": "4B",
    "colonia": "Centro",
    "ciudad": "Ciudad de México",
    "estado": "CDMX",
    "pais": "México",
    "codigo_postal": "06000",
    "referencias": "Edificio azul"
  },
  "creado_en": "2026-11-04T18:30:00Z",
  "actualizado_en": "2026-11-05T09:00:00Z"
}
```

### 16.5 Actualizar envío

```http
PUT /api/admin/envios/801
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "estado": "en_transito",
  "paqueteria_id": 1,
  "numero_guia": "DEMO-123456",
  "url_seguimiento": "https://paqueteria.example/tracking/DEMO-123456"
}
```

### 16.6 Decisiones pendientes de envíos

- Tarifas por peso, zona, código postal, paquetería o monto fijo.
- Cálculo de peso total.
- Tiempo estimado de entrega.
- Integración con paqueterías o actualización manual.
- Estados de envío.
- Política de envío gratis.
- Dirección editable después de crear el pedido.
- Impuestos y aranceles internacionales.

---

## 17. Reportes y tickets

### 17.1 Reporte de ventas

```http
GET /api/admin/reportes/ventas?desde=2026-11-01&hasta=2026-11-30&agrupacion=dia
Authorization: Bearer <token-admin>
```

```json
{
  "desde": "2026-11-01",
  "hasta": "2026-11-30",
  "agrupacion": "dia",
  "moneda": "MXN",
  "totales": {
    "pedidos": 120,
    "ventas_brutas": 215000.0,
    "descuentos": 8500.0,
    "envios": 12000.0,
    "reembolsos": 3500.0,
    "ventas_netas": 215000.0
  },
  "series": [
    {
      "periodo": "2026-11-01",
      "pedidos": 5,
      "ventas_netas": 9500.0
    }
  ]
}
```

### 17.2 Reporte por producto

```http
GET /api/admin/reportes/productos?desde=2026-11-01&hasta=2026-11-30
Authorization: Bearer <token-admin>
```

```json
{
  "datos": [
    {
      "producto_id": 12,
      "sku": "BAG-TOT-001",
      "nombre": "Tote Bag Aurora",
      "unidades_vendidas": 30,
      "ventas_netas": 26970.0,
      "devoluciones": 2
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

### 17.3 Decisiones pendientes de reportes

- Qué se considera venta: pedido creado, pagado o entregado.
- Tratamiento de impuestos, envíos, descuentos y reembolsos.
- Zona horaria de agrupación.
- Moneda y conversión.
- Permisos de exportación.
- Formato de ticket y datos fiscales.

---

## 18. Reseñas

### 18.1 Crear reseña

```http
POST /api/productos/12/resenas
Authorization: Bearer <token-cliente>
Content-Type: application/json
```

```json
{
  "calificacion": 5,
  "titulo": "Excelente calidad",
  "comentario": "La bolsa es amplia y resistente.",
  "pedido_id": 501
}
```

Respuesta `201 Created`:

```json
{
  "id": 301,
  "producto_id": 12,
  "cliente_id": 15,
  "pedido_id": 501,
  "calificacion": 5,
  "titulo": "Excelente calidad",
  "comentario": "La bolsa es amplia y resistente.",
  "estado": "pendiente",
  "creado_en": "2026-11-06T12:00:00Z"
}
```

### 18.2 Reseñas públicas

```http
GET /api/productos/12/resenas?pagina=1&por_pagina=20
```

```json
{
  "datos": [
    {
      "id": 301,
      "calificacion": 5,
      "titulo": "Excelente calidad",
      "comentario": "La bolsa es amplia y resistente.",
      "cliente": {
        "id": 15,
        "nombre": "Ana P."
      },
      "creado_en": "2026-11-06T12:00:00Z"
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

### 18.3 Moderación

```http
PUT /api/admin/resenas/301
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "estado": "publicada",
  "nota_moderacion": "Revisada"
}
```

Estados propuestos: `pendiente`, `publicada`, `rechazada`.

Decisiones pendientes:

- Compra verificada obligatoria o opcional.
- Una reseña por producto/cliente/pedido.
- Edición y eliminación por parte del cliente.
- Moderación previa o posterior.
- Mostrar nombre completo o abreviado.

---

## 19. Devoluciones, reembolsos y reposición

### 19.1 Solicitar devolución

```http
POST /api/pedidos/501/devoluciones
Authorization: Bearer <token-cliente>
Content-Type: application/json
```

```json
{
  "items": [
    {
      "pedido_item_id": 9001,
      "cantidad": 1,
      "motivo": "producto_defectuoso",
      "comentario": "La costura llegó abierta."
    }
  ],
  "motivo": "producto_defectuoso"
}
```

Respuesta `201 Created`:

```json
{
  "id": 401,
  "pedido_id": 501,
  "cliente_id": 15,
  "estado": "solicitada",
  "motivo": "producto_defectuoso",
  "monto_solicitado": 899.0,
  "monto_aprobado": null,
  "items": [
    {
      "pedido_item_id": 9001,
      "cantidad": 1,
      "condicion": "defectuoso",
      "reponer_inventario": false
    }
  ],
  "creado_en": "2026-11-08T10:00:00Z"
}
```

### 19.2 Resolver devolución

```http
PUT /api/admin/devoluciones/401/estado
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "estado": "aprobada",
  "monto_aprobado": 899.0,
  "motivo": "Procedente",
  "reponer_inventario": true
}
```

### 19.3 Reembolso

```http
POST /api/admin/devoluciones/401/reembolsos
Authorization: Bearer <token-admin>
Content-Type: application/json
```

```json
{
  "pago_id": 7001,
  "monto": 899.0,
  "metodo": "transferencia",
  "referencia_externa": "REF-2026-001"
}
```

### 19.4 Estados propuestos

```text
solicitada
en_revision
aprobada
rechazada
recibida
reembolsada
cancelada
```

### 19.5 Reglas transaccionales

- La devolución debe validar que el pedido pertenece al cliente.
- La cantidad devuelta no puede exceder la comprada.
- No se puede reembolsar dos veces la misma devolución.
- La reposición de inventario debe ser idempotente.
- La devolución puede requerir recepción física antes del reembolso.
- El reembolso debe asociarse a un pago y a una referencia externa.

### 19.6 Decisiones pendientes

- Ventana de devolución.
- Condiciones del producto.
- Quién paga el envío de retorno.
- Reembolso total o parcial.
- Reembolso al método original o a tienda.
- Reposición automática o manual.
- Tratamiento de productos defectuosos.
- Estados exactos.

---

## 20. Formato de errores

Todos los errores mantienen la estructura:

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

### 20.1 Códigos existentes

| Código | HTTP | Uso |
|---|---:|---|
| `SOLICITUD_INVALIDA` | 400 | Parámetros incompatibles o mal formados |
| `NO_AUTENTICADO` | 401 | Falta autenticación o credenciales inválidas |
| `ACCESO_DENEGADO` | 403 | Sin permisos suficientes |
| `RECURSO_NO_ENCONTRADO` | 404 | Recurso inexistente o no visible |
| `CONFLICTO_UNICIDAD` | 409 | SKU, slug, nombre, email o clave duplicada |
| `CONFLICTO_DEPENDENCIAS` | 409 | Dependencias al desactivar o eliminar |
| `VALIDACION_FALLIDA` | 422 | Errores de validación |
| `ERROR_INTERNO` | 500 | Error no controlado |

### 20.2 Códigos nuevos propuestos

Estos códigos requieren aprobación:

| Código | HTTP | Uso |
|---|---:|---|
| `SESION_EXPIRADA` | 401 | Token o sesión vencida |
| `CREDENCIALES_INVALIDAS` | 401 | Login incorrecto |
| `STOCK_INSUFICIENTE` | 409 | Inventario insuficiente |
| `PEDIDO_DUPLICADO` | 409 | Clave de idempotencia de pedido repetida |
| `CONFLICTO_IDEMPOTENCIA` | 409 | Misma clave con cuerpo distinto |
| `TRANSICION_ESTADO_INVALIDA` | 409 | Cambio de estado no permitido |
| `PAGO_INVALIDO` | 422 | Datos de pago inválidos |
| `CONFLICTO_PAGO` | 409 | Pago duplicado o ya verificado |
| `ARCHIVO_INVALIDO` | 422 | Archivo no permitido |
| `ARCHIVO_DEMASIADO_GRANDE` | 413 | Archivo excede el límite |
| `RESENA_DUPLICADA` | 409 | Reseña duplicada |
| `DEVOLUCION_NO_PERMITIDA` | 409 | Devolución fuera de política |
| `TARIFA_NO_DISPONIBLE` | 422 | No hay tarifa para la dirección o peso |
| `PAQUETERIA_NO_DISPONIBLE` | 409 | Paquetería inactiva |
| `CONFLICTO_CONCURRENCIA` | 409 | Conflicto transaccional |

### 20.3 Ejemplo de error de stock

```json
{
  "error": {
    "codigo": "STOCK_INSUFICIENTE",
    "mensaje": "No hay existencias suficientes para completar el pedido.",
    "detalles": [
      {
        "campo": "items.0.cantidad",
        "mensaje": "Solicitaste 2 unidades y solo hay 1 disponible."
      }
    ]
  }
}
```

---

## 21. Códigos HTTP

| Código | Uso |
|---|---|
| 200 OK | Consulta o actualización exitosa |
| 201 Created | Recurso creado; incluye `Location` cuando aplique |
| 204 No Content | Eliminación o logout exitoso |
| 400 Bad Request | Parámetros incompatibles o mal formados |
| 401 Unauthorized | Falta autenticación o credenciales inválidas |
| 403 Forbidden | Sin permisos |
| 404 Not Found | Recurso inexistente o no visible |
| 409 Conflict | Duplicados, dependencias, stock, idempotencia o transiciones |
| 413 Payload Too Large | Archivo demasiado grande |
| 415 Unsupported Media Type | Tipo de archivo no permitido |
| 422 Unprocessable Entity | Validación de campos |
| 500 Internal Server Error | Error no controlado |
| 503 Service Unavailable | Dependencia externa no disponible, si se aprueba |

---

## 22. Validaciones transversales

1. Recortar espacios al inicio y al final de cadenas.
2. Rechazar cadenas vacías cuando el campo sea obligatorio.
3. Normalizar slugs: minúsculas, sin acentos, guiones simples.
4. Rechazar campos desconocidos en cuerpos de creación y actualización.
5. Precio finito, positivo, máximo dos decimales.
6. IDs enteros positivos.
7. Listas de IDs sin duplicados.
8. Paginación: `pagina >= 1`, `por_pagina` entre 1 y 100.
9. Estados solo dentro del catálogo aprobado.
10. Fechas UTC en respuestas.
11. No aceptar del cliente campos calculados: `id`, `total`, `disponible`, `creado_en`, `actualizado_en`, `total_productos`, stock final, etc.
12. `POST` devuelve `Location` cuando corresponda.
13. `PUT` exige reemplazo completo.
14. Escrituras administrativas requieren rol `administrador`.
15. Los recursos de otros clientes devuelven `404`.
16. No exponer trazas internas ni mensajes sensibles.
17. Validar archivos por contenido, no solo por extensión.
18. Validar idempotencia antes de ejecutar efectos secundarios.

---

## 23. Entidades y relaciones para PostgreSQL

### 23.1 Catálogo existente

- `categorias`
- `productos`
- `colecciones`
- `producto_coleccion`

### 23.2 Nuevas entidades

| Entidad | Campos principales | Relaciones |
|---|---|---|
| `usuarios` | id, email, password_hash, nombre, telefono, rol, estado, timestamps | 1:N pedidos, reseñas, sesiones |
| `sesiones` | id, usuario_id, token_hash, expira_en, revocado_en, user_agent, ip | N:1 usuarios |
| `colores` | id, nombre, slug, codigo_hex, estado, timestamps | 1:N o N:M productos |
| `producto_colores` | producto_id, color_id | N:M productos-colores |
| `imagenes_producto` | id, producto_id, url, storage_key, texto_alternativo, orden, es_principal, timestamps | N:1 productos |
| `inventario_movimientos` | id, producto_id, tipo, cantidad, motivo, stock_anterior, stock_nuevo, referencia, usuario_id, creado_en | N:1 productos/usuarios |
| `pedidos` | id, numero, cliente_id, estado, subtotal, descuento_total, envio_total, total, moneda, idempotency_key, timestamps | N:1 usuarios; 1:N items/pagos/envíos/devoluciones |
| `pedido_items` | id, pedido_id, producto_id, sku, nombre, color, precio_unitario, cantidad, descuento_unitario, subtotal, moneda | N:1 pedidos; producto opcional |
| `pedido_estado_historial` | id, pedido_id, estado_anterior, estado_nuevo, motivo, usuario_id, creado_en | N:1 pedidos/usuarios |
| `pagos` | id, pedido_id, metodo, proveedor, referencia_externa, monto, moneda, estado, verificado_en, timestamps | N:1 pedidos |
| `pago_estado_historial` | id, pago_id, estado_anterior, estado_nuevo, motivo, usuario_id, creado_en | N:1 pagos/usuarios |
| `paqueterias` | id, nombre, slug, activo, url_seguimiento_plantilla, timestamps | 1:N envíos/tarifas |
| `tarifas_envio` | id, paqueteria_id, nombre, zona, rango_cp, rango_peso, precio, moneda, activo, vigencia | N:1 paqueterías |
| `envios` | id, pedido_id, paqueteria_id, estado, numero_guia, url_seguimiento, costo, destinatario, direccion, telefono, timestamps | N:1 pedidos/paqueterías |
| `resenas` | id, producto_id, cliente_id, pedido_id, calificacion, titulo, comentario, estado, timestamps | N:1 productos/usuarios/pedidos |
| `devoluciones` | id, pedido_id, cliente_id, estado, motivo, monto_solicitado, monto_aprobado, timestamps | N:1 pedidos/usuarios; 1:N items/reembolsos |
| `devolucion_items` | id, devolucion_id, pedido_item_id, cantidad, condicion, reponer_inventario | N:1 devoluciones/pedido_items |
| `reembolsos` | id, devolucion_id, pago_id, monto, moneda, estado, referencia, timestamps | N:1 devoluciones/pagos |
| `idempotencia` | id, usuario_id, clave, endpoint, hash_request, respuesta_id, estado, expira_en, creado_en | N:1 usuarios |

### 23.3 Restricciones e índices propuestos

- `usuarios.email` único sin distinguir mayúsculas.
- `colores.nombre` y `colores.slug` únicos.
- `productos.sku` y `productos.slug` únicos, incluso con borrado lógico según decisión.
- `categorias.nombre/slug` únicos.
- `colecciones.nombre/slug` únicos.
- `producto_coleccion` clave primaria compuesta.
- `producto_colores` clave primaria compuesta.
- `imagenes_producto` orden único por producto si se aprueba.
- `pedidos.idempotency_key` único por usuario.
- `pedidos.numero` único.
- `pagos.referencia_externa` único por proveedor si existe.
- `resenas` única por producto/cliente/pedido según decisión.
- Índices por estado, fechas, categoría, colección, color, cliente y referencias.
- `timestamptz` con zona horaria UTC.
- Decisiones de `ON DELETE` por entidad.

### 23.4 Decisiones de PostgreSQL

- PK entero vs UUID.
- Precio `NUMERIC(10,2)` vs centavos.
- Moneda fija vs columna.
- Borrado lógico vs físico por entidad.
- Inventario por producto, color o variante.
- Uso de `existencias` como columna o cálculo desde movimientos.
- Índices y particiones para pedidos y reportes.
- Herramienta de migraciones.
- Nivel de aislamiento.
- Estrategia de respaldo y restauración.

---

## 24. Transacciones, bloqueo e idempotencia

| Operación | Transacción | Bloqueo | Idempotencia |
|---|---|---|---|
| Crear pedido | Sí | Inventario con `FOR UPDATE` | `Idempotency-Key` |
| Confirmar pago | Sí | Pago/pedido | Referencia única |
| Ajustar inventario | Sí | Fila de inventario | Referencia opcional |
| Devolución | Sí | Devolución/pedido | Clave o estado condicional |
| Reposición | Sí | Inventario | Una sola vez por devolución |
| Reembolso | Sí | Pago/devolución | Referencia única |
| Actualizar envío | Sí | Envío | ID de evento externo |
| Subir imagen | Parcial | No aplica | Hash o clave de subida |
| Crear reseña | Sí | No aplica | Restricción única |
| Crear color | Sí | No aplica | Restricción única |

### 24.1 Flujo recomendado de confirmación de pedido

1. Autenticar cliente.
2. Validar idempotencia.
3. Iniciar transacción.
4. Bloquear filas de productos/inventario.
5. Verificar stock.
6. Calcular montos en servidor.
7. Crear pedido e items históricos.
8. Descontar o reservar stock.
9. Registrar movimiento de inventario.
10. Registrar clave de idempotencia.
11. Confirmar transacción.
12. Devolver pedido.

### 24.2 Conflictos

- Si dos clientes compran el último producto, solo una transacción debe completar.
- La otra debe recibir `409 STOCK_INSUFICIENTE`.
- Si la misma `Idempotency-Key` se reutiliza con el mismo cuerpo, devolver la misma respuesta.
- Si se reutiliza con otro cuerpo, devolver `409 CONFLICTO_IDEMPOTENCIA`.
- Si falla una transacción, no debe quedar stock descontado ni pedido parcial.

---

## 25. Decisiones pendientes

### 25.1 Base de datos

- **DB-01:** PK entero o UUID.
- **DB-02:** precio decimal o centavos.
- **DB-03:** moneda fija o por operación.
- **DB-04:** inventario por producto o por variante.
- **DB-05:** `existencias` como columna o cálculo desde movimientos.
- **DB-06:** política de borrado por entidad.
- **DB-07:** restricciones únicas.
- **DB-08:** índices y particiones.
- **DB-09:** herramienta de migraciones.
- **DB-10:** aislamiento y bloqueo.
- **DB-11:** reservas de inventario y expiración.
- **DB-12:** orden de productos en colecciones.

### 25.2 Frontend

- **FE-01:** mecanismo de autenticación y almacenamiento de token.
- **FE-02:** pantallas de registro, login y sesión.
- **FE-03:** formato de imágenes y límites.
- **FE-04:** selección de colores y filtros combinados.
- **FE-05:** flujo de carrito y checkout.
- **FE-06:** campos exactos de entrega.
- **FE-07:** visualización de estados de pedido, pago y envío.
- **FE-08:** reportes y tickets.
- **FE-09:** reseñas y devoluciones.
- **FE-10:** orígenes CORS definitivos.
- **FE-11:** manejo visual de errores 401, 403, 409 y 422.

### 25.3 Negocio

- **NG-01:** pasarela de pago.
- **NG-02:** métodos de pago.
- **NG-03:** política de envíos y tarifas.
- **NG-04:** política de devoluciones y reembolsos.
- **NG-05:** descuentos y cupones.
- **NG-06:** pedidos como invitado.
- **NG-07:** compra verificada para reseñas.
- **NG-08:** estados oficiales.
- **NG-09:** cancelaciones.
- **NG-10:** sobreventa o backorder.
- **NG-11:** impuestos y facturación.
- **NG-12:** creación y recuperación de administradores.

### 25.4 Contrato y API

- **API-01:** mantener `/api` o introducir `/api/v1`.
- **API-02:** filtros de color en endpoint existente o subrecurso de color.
- **API-03:** exponer colores en respuesta de producto o subrecurso separado.
- **API-04:** aceptar imágenes por URL, por ID o ambas.
- **API-05:** códigos de error nuevos.
- **API-06:** forma de idempotencia: cabecera o cuerpo.
- **API-07:** estructura de reportes.
- **API-08:** respuesta de productos en colección administrativa.
- **API-09:** paginación de subrecursos.
- **API-10:** si las rutas administrativas usan prefijo `/api/admin`.

---

## 26. Compatibilidad con 0.2.0

- Los endpoints de catálogo existentes no cambian de ruta.
- Las respuestas públicas de productos, categorías y colecciones se mantienen.
- Las escrituras de catálogo siguen siendo administrativas.
- El campo `imagenes` de producto se conserva.
- `existencias` se conserva en producto mientras se define la migración a inventario.
- Las colecciones siguen administrándose por `producto_ids`.
- Los nuevos módulos se exponen en rutas nuevas.
- Cualquier cambio de forma en respuestas existentes requiere una versión mayor o una estrategia de compatibilidad.
- La propuesta no elimina funcionalidades de 0.2.0.

---

## 27. Fuera de alcance

- Implementación de código.
- Conexión real a PostgreSQL.
- Modelos SQLAlchemy.
- Migraciones.
- Integración real con pasarelas de pago.
- Integración real con paqueterías.
- Facturación fiscal.
- Cupones y promociones, salvo que se aprueben.
- Recomendaciones personalizadas.
- Búsqueda avanzada.
- Aplicaciones móviles.
- Autenticación multifactor.

---

## 28. Checklist de aprobación

Antes de convertir esta propuesta en contrato definitivo:

- [ ] Confirmar versión 0.3.0.
- [ ] Aprobar mecanismo de autenticación.
- [ ] Aprobar modelo de roles.
- [ ] Aprobar relación producto-color.
- [ ] Aprobar almacenamiento de imágenes.
- [ ] Aprobar fuente de verdad del inventario.
- [ ] Aprobar estados de pedido, pago, envío y devolución.
- [ ] Aprobar política de idempotencia.
- [ ] Aprobar reglas de envío y tarifas.
- [ ] Aprobar pasarela de pago.
- [ ] Aprobar política de devoluciones y reembolsos.
- [ ] Aprobar compra verificada para reseñas.
- [ ] Aprobar códigos de error nuevos.
- [ ] Aprobar decisiones de PostgreSQL.
- [ ] Aprobar estructura final de endpoints.
- [ ] Confirmar que no se modificarán endpoints existentes de forma incompatible.
- [ ] Autorizar la creación del contrato definitivo.
