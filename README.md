# BagStore API

Backend de BagStore construido con Python, FastAPI y Pydantic. En esta fase no existe conexión a PostgreSQL: los productos, categorías y colecciones se almacenan temporalmente en memoria y los datos se pierden al reiniciar el servidor.

## Requisitos

- Python 3.12
- Entorno virtual `.venv`

## Instalación

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Si no existe `.env`, créalo a partir de `.env.example`:

```powershell
Copy-Item .env.example .env
```

## Ejecución

```powershell
python -m uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000/api`
- Health: `http://127.0.0.1:8000/api/health`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Pruebas

```powershell
python -m pytest
```

Las pruebas usan repositorios temporales aislados y limpian su estado antes y después de cada caso. No requieren PostgreSQL ni servicios externos.

Para generar el reporte de cobertura:

```powershell
python -m pytest --cov=app --cov-report=term-missing
```

## Estructura

```text
app/
├── main.py
├── api/
│   ├── deps.py
│   ├── router.py
│   └── routes/
│       ├── health.py
│       ├── productos.py
│       ├── categorias.py
│       └── colecciones.py
├── core/
│   ├── config.py
│   └── errors.py
├── schemas/
│   ├── common.py
│   ├── errors.py
│   ├── health.py
│   ├── imagen.py
│   ├── categoria.py
│   ├── coleccion.py
│   └── producto.py
├── models/
├── services/
│   ├── productos.py
│   ├── categorias.py
│   └── colecciones.py
└── repositories/
    ├── categorias.py
    ├── colecciones.py
    └── productos.py
tests/
docs/api-contract.md
```

## Endpoints

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

### Categorías

Listar categorías:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/categorias?estado=activo&pagina=1&por_pagina=20"
```

Crear categoría:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/categorias" `
  -ContentType "application/json" `
  -Body '{
    "nombre": "Bandoleras",
    "descripcion": "Bolsas bandolera.",
    "estado": "activo",
    "orden": 4
  }'
```

Reemplazar categoría:

```powershell
Invoke-RestMethod -Method Put `
  -Uri "http://127.0.0.1:8000/api/categorias/1" `
  -ContentType "application/json" `
  -Body '{
    "nombre": "Cross Body Premium",
    "descripcion": "Bolsas cross body premium.",
    "estado": "activo",
    "orden": 2
  }'
```

### Colecciones

Listar colecciones:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/colecciones?estado=activo&pagina=1&por_pagina=20"
```

Crear colección:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/colecciones" `
  -ContentType "application/json" `
  -Body '{
    "nombre": "Verano",
    "descripcion": "Selección de verano.",
    "estado": "activo",
    "producto_ids": [1, 3, 4]
  }'
```

Reemplazar membresía de una colección:

```powershell
Invoke-RestMethod -Method Put `
  -Uri "http://127.0.0.1:8000/api/colecciones/1" `
  -ContentType "application/json" `
  -Body '{
    "nombre": "La Colección",
    "estado": "activo",
    "producto_ids": [1, 2, 5]
  }'
```

Obtener productos de una colección:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/productos?coleccion=la-coleccion&pagina=1&por_pagina=20"
```

## Datos iniciales

- 10 productos distribuidos entre Tote Bags, Cross Body y Mini Bags.
- Productos disponibles y agotados.
- Productos activos e inactivos.
- Productos con y sin imágenes.
- 3 categorías: `tote-bags`, `cross-body` y `mini-bags`.
- 2 colecciones: `la-coleccion` activa y `archivo` inactiva.

## Relación producto-colección

La única fuente canónica de la relación es `producto_ids` en `/api/colecciones`.

- El producto expone `colecciones` como campo de solo lectura.
- No existe `coleccion_ids` en las solicitudes de producto.
- Los productos de una colección se consultan con `GET /api/productos?coleccion=...`.
- El detalle de colección no incluye productos embebidos.
- Eliminar una colección elimina únicamente sus asociaciones.
- Eliminar un producto lo elimina de todas sus colecciones.

## Reglas actuales de acceso

- `GET` público solo devuelve productos, categorías y colecciones activas.
- Los productos agotados siguen visibles si están activos, con `disponible=false`.
- Los recursos inactivos devuelven `404` en el detalle público.
- `estado=inactivo` y `estado=todos` devuelven `403` sin autenticación.
- Las escrituras están temporalmente abiertas mediante una dependencia no-op. La autenticación se implementará en una fase posterior.

## Alcance actual

- Aplicación FastAPI con prefijo `/api`.
- Health, Swagger, CORS configurable y errores normalizados.
- Repositorios temporales de productos, categorías y colecciones.
- Servicios con validaciones de negocio y conteos.
- CRUD temporal de productos, categorías y colecciones.
- Filtros, paginación y ordenamiento.
- Borrado lógico de productos y borrado físico de categorías/colecciones.
- Validación de dependencias y relaciones.

No se implementan todavía PostgreSQL, SQLAlchemy, migraciones, autenticación, pagos, carrito ni compras.

## Decisiones pendientes

- Tipo definitivo de PK (entero o UUID).
- Representación definitiva de precios y moneda en la base de datos.
- Almacenamiento de imágenes y posible subida de archivos.
- Estrategia definitiva de borrado lógico en PostgreSQL.
- Generación y resolución de colisiones de slugs en la base de datos.
- Índices y restricciones `UNIQUE` definitivas.
- Implementación de autenticación y autorización del administrador.
- Orígenes CORS definitivos del frontend.
