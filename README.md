# BagStore API

Backend de BagStore construido con Python, FastAPI, SQLAlchemy y PostgreSQL. La autenticación usa sesiones opacas con tokens Bearer almacenados de forma segura. El catálogo de productos, categorías y colecciones ya se persiste en PostgreSQL.

## Requisitos

- Python 3.12
- PostgreSQL 15 o superior
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

## Configuración

Variables principales:

```text
DATABASE_URL=postgresql+psycopg://bagstore:bagstore@localhost:5432/bagstore
DATABASE_ECHO=false
SESSION_TTL_MINUTES=1440
ADMIN_EMAIL=admin@bagstore.com
ADMIN_PASSWORD=cambiar-en-desarrollo
```

### Crear la base de datos

Ejemplo con `psql`:

```sql
CREATE USER bagstore WITH PASSWORD 'bagstore';
CREATE DATABASE bagstore OWNER bagstore;
```

Ajusta usuario, contraseña, host y base de datos en `DATABASE_URL`.

## Migraciones

```powershell
python -m alembic upgrade head
```

Para revertir la migración inicial:

```powershell
python -m alembic downgrade base
```

## Datos iniciales

```powershell
python -m app.scripts.seed
```

El seed carga:

- 3 categorías.
- 2 colecciones.
- 10 productos con imágenes y relaciones.
- Un administrador si `ADMIN_PASSWORD` está definida.

El seed es idempotente: no duplica el catálogo si ya existen categorías.

## Ejecución

```powershell
python -m uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000/api`
- Health: `http://127.0.0.1:8000/api/health`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Autenticación

```text
POST /api/auth/registro
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/sesion
```

Registro:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/auth/registro" `
  -ContentType "application/json" `
  -Body '{
    "nombre": "Ana Pérez",
    "email": "ana@bagstore.com",
    "password": "una-contraseña-segura",
    "telefono": "+5215512345678"
  }'
```

Login:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/auth/login" `
  -ContentType "application/json" `
  -Body '{
    "email": "ana@bagstore.com",
    "password": "una-contraseña-segura"
  }'
```

La respuesta incluye `access_token`. Para las rutas protegidas:

```http
Authorization: Bearer <access_token>
```

Las escrituras de catálogo y las lecturas administrativas requieren rol `administrador`.

## Endpoints

```text
GET    /api/health

POST   /api/auth/registro
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/sesion

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

Los ejemplos de escritura omiten la cabecera `Authorization` por brevedad, pero es obligatoria.

## Pruebas

```powershell
python -m pytest
```

Por defecto las pruebas usan SQLite en memoria para ejecutarse sin un servidor PostgreSQL. La suite limpia y recrea el esquema antes de cada prueba.

Para ejecutar también las pruebas de integración con PostgreSQL, usa una base de datos **dedicada** a pruebas:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://bagstore:bagstore@localhost:5432/bagstore_test"
python -m pytest
```

Advertencia: las pruebas de PostgreSQL destruyen y recrean las tablas de la base indicada. No uses la base de desarrollo.

Cobertura:

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
│       ├── auth.py
│       ├── productos.py
│       ├── categorias.py
│       └── colecciones.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── enums.py
│   ├── errors.py
│   ├── security.py
│   └── text.py
├── models/
│   ├── usuario.py
│   ├── sesion.py
│   ├── categoria.py
│   ├── producto.py
│   ├── imagen.py
│   ├── coleccion.py
│   └── producto_coleccion.py
├── schemas/
│   ├── auth.py
│   ├── common.py
│   ├── errors.py
│   ├── health.py
│   ├── imagen.py
│   ├── categoria.py
│   ├── coleccion.py
│   └── producto.py
├── services/
│   ├── auth.py
│   ├── productos.py
│   ├── categorias.py
│   └── colecciones.py
├── repositories/
│   ├── categorias.py
│   ├── colecciones.py
│   ├── productos.py
│   ├── usuarios.py
│   ├── sesiones.py
│   └── sqlalchemy/
│       ├── productos.py
│       ├── categorias.py
│       ├── colecciones.py
│       ├── usuarios.py
│       ├── sesiones.py
│       └── mapeadores.py
└── scripts/
    └── seed.py
alembic/
tests/
docs/
```

Los repositorios en memoria de catálogo se conservan como referencia y utilidad de seed/pruebas. La API usa exclusivamente los repositorios SQLAlchemy.

## Reglas actuales de acceso

- `GET` público solo devuelve productos, categorías y colecciones activas.
- Un administrador autenticado puede consultar recursos inactivos y usar `estado=inactivo` o `estado=todos`.
- Un cliente autenticado sigue viendo únicamente el catálogo público.
- Los productos agotados siguen visibles si están activos, con `disponible=false`.
- Los recursos inactivos devuelven `404` a visitantes y clientes.
- Las escrituras requieren rol `administrador`.
- Las sesiones expiran y pueden revocarse con logout.
- Las contraseñas se almacenan con Argon2id.

## Alcance actual

- PostgreSQL con SQLAlchemy y Alembic.
- Modelos de usuarios, sesiones, categorías, productos, imágenes y colecciones.
- Persistencia real del catálogo.
- Registro de clientes, login, logout y sesión activa.
- Tokens Bearer opacos con hash en base de datos.
- Roles `cliente` y `administrador`.
- Protección de escrituras administrativas.
- CRUD persistente de productos, categorías y colecciones.
- Seed de datos iniciales.
- Pruebas de API, servicios, repositorios, autenticación y persistencia.

No se implementan todavía pagos, pedidos, envíos ni devoluciones.

## Decisiones pendientes

- Tipo definitivo de PK para el resto de módulos.
- Moneda y representación definitiva de precios.
- Almacenamiento externo de imágenes y subida de archivos.
- Inventario basado en movimientos.
- Jerarquía de categorías.
- Orden de productos dentro de colecciones.
- Recuperación de contraseña y verificación de correo.
- Orígenes CORS definitivos.
- Estrategia de migración para las fases de pedidos, pagos y envíos.
