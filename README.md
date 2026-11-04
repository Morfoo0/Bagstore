# BagStore API

Backend de BagStore construido con Python, FastAPI y Pydantic. En esta fase no existe conexión a PostgreSQL: los productos se almacenan temporalmente en memoria y los datos se pierden al reiniciar el servidor.

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

## Estructura

```text
app/
├── main.py
├── api/
│   ├── deps.py
│   ├── router.py
│   └── routes/
│       ├── health.py
│       └── productos.py
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
│   └── productos.py
└── repositories/
    ├── categorias.py
    ├── colecciones.py
    └── productos.py
tests/
docs/api-contract.md
```

## Endpoints de productos

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/productos` | Lista pública con filtros, paginación y ordenamiento |
| GET | `/api/productos/{id}` | Detalle público de un producto activo |
| POST | `/api/productos` | Crea un producto. Responde `201` y `Location` |
| PUT | `/api/productos/{id}` | Reemplaza el producto completo |
| DELETE | `/api/productos/{id}` | Borrado lógico. Responde `204` |

### Ejemplos

Listar productos activos:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/productos?pagina=1&por_pagina=5"
```

Filtrar por categoría, disponibilidad y precio:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/productos?categoria=tote-bags&disponible=true&orden=precio_asc"
```

Filtrar por colección:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/productos?coleccion=la-coleccion"
```

Obtener detalle:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/productos/1"
```

Crear producto:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/productos" `
  -ContentType "application/json" `
  -Body '{
    "nombre": "Tote Bag Nueva",
    "precio": "899.00",
    "sku": "BAG-NEW-001",
    "categoria_id": 2,
    "existencias": 10
  }'
```

Reemplazar producto:

```powershell
Invoke-RestMethod -Method Put `
  -Uri "http://127.0.0.1:8000/api/productos/1" `
  -ContentType "application/json" `
  -Body '{
    "nombre": "Tote Bag Aurora",
    "precio": "950.00",
    "categoria_id": 2,
    "existencias": 0,
    "imagenes": [],
    "estado": "activo"
  }'
```

Eliminar producto:

```powershell
Invoke-WebRequest -Method Delete `
  -Uri "http://127.0.0.1:8000/api/productos/1" `
  -UseBasicParsing
```

## Datos iniciales

El repositorio en memoria incluye:

- 10 productos distribuidos entre Tote Bags, Cross Body y Mini Bags.
- Productos disponibles y agotados.
- Productos activos e inactivos.
- Productos con y sin imágenes.
- Productos asociados a las colecciones `la-coleccion` y `archivo`.
- 3 categorías y 2 colecciones de referencia.

## Reglas actuales de acceso

- `GET /api/productos` solo devuelve productos activos.
- Los productos agotados siguen visibles si están activos, con `disponible=false`.
- Los productos inactivos devuelven `404` en el detalle público.
- `estado=inactivo` y `estado=todos` devuelven `403` sin autenticación.
- Las escrituras están temporalmente abiertas mediante una dependencia no-op. La autenticación se implementará en una fase posterior.

## Alcance actual

- Aplicación FastAPI con prefijo `/api`.
- Health, Swagger, CORS configurable y errores normalizados.
- Repositorios temporales de productos, categorías y colecciones.
- Servicio de productos con validaciones de negocio.
- CRUD temporal de productos.
- Filtros, paginación y ordenamiento.
- Borrado lógico con reserva de SKU y slug.

No se implementan todavía PostgreSQL, SQLAlchemy, migraciones, autenticación, endpoints de categorías/colecciones, pagos, carrito ni compras.

## Decisiones pendientes

- Tipo definitivo de PK (entero o UUID).
- Representación definitiva de precios y moneda en la base de datos.
- Almacenamiento de imágenes y posible subida de archivos.
- Estrategia definitiva de borrado lógico en PostgreSQL.
- Generación y resolución de colisiones de slugs en la base de datos.
- Índices y restricciones `UNIQUE` definitivas.
- Implementación de autenticación y autorización del administrador.
- Orígenes CORS definitivos del frontend.
