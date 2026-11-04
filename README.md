# BagStore API

Backend de BagStore construido con Python, FastAPI y Pydantic. En esta fase no existe conexión a PostgreSQL: la persistencia se implementará más adelante con almacenamiento temporal en memoria.

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
│   ├── router.py
│   └── routes/
│       └── health.py
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
└── repositories/
tests/
docs/api-contract.md
```

## Alcance actual

- Aplicación FastAPI con prefijo `/api`.
- Endpoint `GET /api/health`.
- Swagger en `/docs`.
- CORS configurable por variables de entorno.
- Configuración centralizada.
- Schemas Pydantic para productos, categorías, colecciones, imágenes, paginación y errores.
- Manejo normalizado de errores con la envoltura `{"error": ...}`.

No se implementan todavía CRUD, PostgreSQL, SQLAlchemy, migraciones, autenticación, pagos, carrito ni compras.

## Decisiones pendientes

- Tipo definitivo de PK (entero o UUID).
- Representación definitiva de precios y moneda en la base de datos.
- Almacenamiento de imágenes y posible subida de archivos.
- Estrategia de borrado lógico de productos.
- Generación y resolución de colisiones de slugs.
- Índices y restricciones `UNIQUE` definitivas.
- Orígenes CORS definitivos del frontend.
