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
UPLOAD_DIR=uploads
MEDIA_BASE_URL=http://localhost:8000/media
MAX_IMAGE_SIZE_BYTES=5242880
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

Para revertir todas las migraciones:

```powershell
python -m alembic downgrade base
```

Migraciones incluidas:

- `f981cd3896fc_initial_schema`
- `0cf537a3b11d_colores_e_imagenes`

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

GET    /api/productos/{id}/colores
PUT    /api/productos/{id}/colores
POST   /api/productos/{id}/imagenes
PUT    /api/productos/{id}/imagenes/{imagen_id}
DELETE /api/productos/{id}/imagenes/{imagen_id}

GET    /api/colores
GET    /api/colores/{id}
POST   /api/colores
PUT    /api/colores/{id}
DELETE /api/colores/{id}

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

GET    /api/admin/colecciones
GET    /api/admin/colecciones/{id}
GET    /api/admin/colecciones/{id}/productos
PUT    /api/admin/productos/{id}/estado
```

Los ejemplos de escritura omiten la cabecera `Authorization` por brevedad, pero es obligatoria.

## Colores

Los colores son atributos compartidos por el producto. Un producto puede tener varios colores y todos comparten el mismo `existencias`; no existe inventario independiente por color.

- `GET /api/colores` es público.
- El CRUD de colores requiere administrador.
- `tono` usa formato hexadecimal `#RRGGBB`.
- Los nombres duplicados se rechazan sin distinguir mayúsculas, minúsculas ni acentos.
- `GET /api/productos?color_id=1` filtra productos por color.
- `PUT /api/productos/{id}/colores` reemplaza la asociación completa.
- No se puede eliminar un color asociado a productos.

## Imágenes

La subida de imágenes requiere administrador:

```text
POST   /api/productos/{id}/imagenes
PUT    /api/productos/{id}/imagenes/{imagen_id}
DELETE /api/productos/{id}/imagenes/{imagen_id}
```

- Formatos permitidos: JPEG, PNG y WebP.
- Tamaño máximo configurable con `MAX_IMAGE_SIZE_BYTES`.
- Máximo 10 imágenes por producto.
- Se valida el contenido real del archivo, no solo la extensión.
- Se generan nombres con UUID y URLs construidas desde `MEDIA_BASE_URL`.
- Los archivos se guardan en `UPLOAD_DIR` y se sirven desde `/media`.

### Almacenamiento local y producción

En desarrollo se usa `AlmacenamientoLocal`, implementado en `app/core/storage.py`. No guarda binarios en PostgreSQL y no devuelve rutas de la computadora del desarrollador.

Para producción se debe implementar la misma interfaz `AlmacenamientoImagen` con S3, R2, GCS u otro proveedor, y configurar `MEDIA_BASE_URL` con el dominio o CDN definitivo. `UPLOAD_DIR` solo aplica al almacenamiento local.

## Administración de catálogo

- `GET /api/admin/colecciones` devuelve colecciones activas e inactivas.
- `GET /api/admin/colecciones/{id}/productos` devuelve productos activos e inactivos de la colección.
- `PUT /api/admin/productos/{id}/estado` activa o desactiva un producto sin eliminar su historial ni sus relaciones.
- `DELETE /api/productos/{id}` sigue siendo un borrado lógico.
- Las consultas públicas mantienen las reglas de visibilidad del catálogo.

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
│       ├── imagenes.py
│       ├── colores.py
│       ├── categorias.py
│       ├── colecciones.py
│       ├── admin_colecciones.py
│       └── admin_productos.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── enums.py
│   ├── errors.py
│   ├── security.py
│   ├── storage.py
│   └── text.py
├── models/
│   ├── usuario.py
│   ├── sesion.py
│   ├── categoria.py
│   ├── color.py
│   ├── producto.py
│   ├── imagen.py
│   ├── coleccion.py
│   ├── producto_coleccion.py
│   └── producto_color.py
├── schemas/
│   ├── auth.py
│   ├── common.py
│   ├── errors.py
│   ├── health.py
│   ├── color.py
│   ├── imagen.py
│   ├── categoria.py
│   ├── coleccion.py
│   └── producto.py
├── services/
│   ├── auth.py
│   ├── productos.py
│   ├── colores.py
│   ├── imagenes.py
│   ├── categorias.py
│   └── colecciones.py
├── repositories/
│   ├── categorias.py
│   ├── colecciones.py
│   ├── productos.py
│   ├── colores.py
│   ├── imagenes.py
│   ├── usuarios.py
│   ├── sesiones.py
│   └── sqlalchemy/
│       ├── productos.py
│       ├── categorias.py
│       ├── colecciones.py
│       ├── colores.py
│       ├── imagenes.py
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
- La subida y eliminación de imágenes requiere rol `administrador`.
- El CRUD de colores requiere rol `administrador`.
- Las consultas administrativas de colecciones y el cambio de estado de productos requieren rol `administrador`.
- Las sesiones expiran y pueden revocarse con logout.
- Las contraseñas se almacenan con Argon2id.

## Alcance actual

- PostgreSQL con SQLAlchemy y Alembic.
- Modelos de usuarios, sesiones, categorías, colores, productos, imágenes y colecciones.
- Persistencia real del catálogo.
- Registro de clientes, login, logout y sesión activa.
- Tokens Bearer opacos con hash en base de datos.
- Roles `cliente` y `administrador`.
- Protección de escrituras administrativas.
- CRUD persistente de productos, categorías, colecciones y colores.
- Asociación muchos-a-muchos entre productos y colores.
- Filtro de productos por `color_id`.
- Subida local de imágenes con validación, orden y principal.
- Consultas administrativas de colecciones con productos activos e inactivos.
- Activación y desactivación administrativa de productos.
- Borrado lógico de productos.
- Seed de datos iniciales.
- Pruebas de API, servicios, repositorios, autenticación, imágenes y persistencia.

No se implementan todavía inventario avanzado, pagos, pedidos, envíos ni devoluciones.

## Decisiones pendientes

- Tipo definitivo de PK para el resto de módulos.
- Moneda y representación definitiva de precios.
- Proveedor de almacenamiento externo para producción; la interfaz local ya existe.
- Inventario basado en movimientos.
- Inventario independiente por color o variante; actualmente el stock es compartido por producto.
- Jerarquía de categorías.
- Orden de productos dentro de colecciones.
- Recuperación de contraseña y verificación de correo.
- Orígenes CORS definitivos.
- Estrategia de migración para las fases de pedidos, pagos y envíos.
