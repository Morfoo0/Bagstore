"""API integrada local de Bagstore. PostgreSQL es la única fuente persistente."""
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import unicodedata
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Annotated, Literal

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
UPLOADS = ROOT/'uploads'
UPLOADS.mkdir(exist_ok=True)
COOKIE = 'bagstore_session'

def config():
    file = ROOT/'.runtime/config.json'
    return json.loads(file.read_text(encoding='utf-8')) if file.exists() else {}

def connect():
    url = os.environ.get('DATABASE_URL') or config().get('database_url')
    if not url: raise RuntimeError('Configura DATABASE_URL o ejecuta backend/bootstrap.py.')
    return psycopg.connect(url,row_factory=dict_row,connect_timeout=5)

def norm(value): return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c)).lower().split())
def slug(value): return re.sub(r'[^a-z0-9]+','-',norm(value)).strip('-') or 'bagstore'
def fail(status, message, campo=None): raise HTTPException(status, {'mensaje':message,'detalles':[{'campo':campo,'mensaje':message}] if campo else []})
def money(n): return Decimal(str(n)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
def hash_password(password):
    salt = secrets.token_hex(16)
    return salt+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex()
def password_matches(password, stored):
    salt, digest = stored.split(':',1)
    return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex(),digest)

def initialize():
    with connect() as db:
        db.execute('SELECT pg_advisory_xact_lock(827361)')
        db.execute((ROOT/'schema.sql').read_text(encoding='utf-8'))
        cfg = config()
        email = os.environ.get('BAGSTORE_ADMIN_EMAIL') or cfg.get('admin_email')
        password = os.environ.get('BAGSTORE_ADMIN_PASSWORD') or cfg.get('admin_password')
        if email and password and not db.execute('SELECT id FROM users WHERE email=%s',(email.lower(),)).fetchone():
            db.execute("INSERT INTO users(name,email,password_hash,role) VALUES('Administración',%s,%s,'administrador')",(email.lower(),hash_password(password)))
        for name,tone in [('Negro','#252220'),('Blanco','#FFFFFF'),('Beige','#CDB89E'),('Café','#805839'),('Rojo','#B83236'),('Rosa','#DFA8B8'),('Azul','#456A97'),('Verde','#71836B'),('Gris','#989898'),('Multicolor','#B28AAB')]:
            db.execute('INSERT INTO colors(nombre,normalized,tono) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(name,norm(name),tone))
        if not db.execute('SELECT 1 FROM categories LIMIT 1').fetchone():
            for i,name in enumerate(['Tote Bags','Cross Body','Mini Bags']): db.execute("INSERT INTO categories(nombre,normalized,slug,orden,estado) VALUES(%s,%s,%s,%s,'activo')",(name,norm(name),slug(name),i))
            for i,(name,price,cat) in enumerate([('Tote Everyday','599',1),('Crossbody Essential','349',2),('Mini Luna','299',3),('Tote Aurora','529',1)]):
                db.execute("INSERT INTO products(nombre,slug,descripcion,precio,sku,categoria_id,color_id,existencias,estado) VALUES(%s,%s,%s,%s,%s,%s,3,20,'activo')",(name,slug(name),'Bolsa del catálogo inicial del proyecto.',price,f'BS-{i+1:03}',cat))
            cid = db.execute("INSERT INTO collections(nombre,normalized,slug,descripcion,estado) VALUES('Everyday essentials','everyday essentials','everyday-essentials','Bolsas para todos tus días.','activo') RETURNING id").fetchone()['id']
            db.execute('INSERT INTO collection_products SELECT %s,id FROM products',(cid,))

@asynccontextmanager
async def lifespan(app):
    initialize()
    yield

app = FastAPI(title='Bagstore integrada',version='1.0.0',lifespan=lifespan)
app.mount('/api/media',StaticFiles(directory=UPLOADS),name='media')

@app.exception_handler(HTTPException)
async def http_error(request, exc):
    body = exc.detail if isinstance(exc.detail,dict) else {'mensaje':str(exc.detail),'detalles':[]}
    return JSONResponse({'error':{'codigo':{401:'NO_AUTENTICADO',403:'ACCESO_DENEGADO',404:'RECURSO_NO_ENCONTRADO',409:'CONFLICTO',422:'VALIDACION_FALLIDA',429:'DEMASIADOS_INTENTOS'}.get(exc.status_code,'SOLICITUD_INVALIDA'),**body}},status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({'error':{'codigo':'VALIDACION_FALLIDA','mensaje':'Revisa los campos señalados.','detalles':[{'campo':'.'.join(str(p) for p in e['loc'][1:]),'mensaje':e['msg']} for e in exc.errors()]}},status_code=422)

@app.exception_handler(psycopg.IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse({'error':{'codigo':'CONFLICTO_DEPENDENCIAS','mensaje':'El registro ya existe o tiene datos relacionados. Revisa la operación.','detalles':[]}},status_code=409)

def database():
    with connect() as db: yield db
DB = Annotated[psycopg.Connection, Depends(database)]

def optional_user(request: Request, db):
    token = request.cookies.get(COOKIE)
    if not token: return None
    return db.execute('SELECT u.id,u.name,u.email,u.role,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s AND s.expires_at>now()',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
def require_user(request, db, admin=False):
    user = optional_user(request,db)
    if not user: fail(401,'Inicia sesión para continuar.')
    if admin and user['role']!='administrador': fail(403,'Necesitas una cuenta administrativa.')
    if request.method not in ('GET','HEAD','OPTIONS'):
        check_origin(request)
        if not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),user['csrf']): fail(403,'La sesión cambió. Actualiza la página e inténtalo de nuevo.')
    return user
def check_origin(request):
    allowed = {os.environ.get('PUBLIC_ORIGIN') or config().get('public_origin','http://127.0.0.1:5173'),'http://localhost:5173','http://127.0.0.1:8001','http://localhost:8001'}
    if request.headers.get('origin') and request.headers['origin'] not in allowed: fail(403,'Origen de solicitud no permitido.')
def is_admin(request,db): return (optional_user(request,db) or {}).get('role')=='administrador'

class Input(BaseModel): model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
class Credentials(Input):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=False)
    email: str = Field(min_length=3,max_length=254)
    password: str = Field(min_length=8,max_length=128)
    @field_validator('email')
    @classmethod
    def email_ok(cls,v):
        v=v.strip()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',v): raise ValueError('Correo electrónico inválido.')
        return v.lower()
class Registration(Credentials):
    name: str = Field(min_length=2,max_length=80)
    @field_validator('name')
    @classmethod
    def name_ok(cls,v):
        if len(v.strip())<2:raise ValueError('Escribe tu nombre.')
        return v.strip()

def session_response(user, db, response):
    token, csrf = secrets.token_urlsafe(40),secrets.token_urlsafe(32)
    db.execute("DELETE FROM sessions WHERE expires_at<now()")
    db.execute("INSERT INTO sessions(token_hash,user_id,csrf,expires_at) VALUES(%s,%s,%s,now()+interval '12 hours')",(hashlib.sha256(token.encode()).hexdigest(),user['id'],csrf))
    response.set_cookie(COOKIE,token,httponly=True,samesite='strict',secure=os.environ.get('COOKIE_SECURE')=='1',max_age=43200,path='/')
    return {'user':{k:user[k] for k in ('id','name','email','role')},'csrf':csrf}

@app.post('/api/auth/register',status_code=201)
def register(value: Registration, request: Request, response: Response, db: DB):
    check_origin(request)
    if db.execute('SELECT 1 FROM users WHERE email=%s',(value.email,)).fetchone(): fail(409,'Este correo ya tiene una cuenta.','email')
    user = db.execute('INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s) RETURNING id,name,email,role',(value.name,value.email,hash_password(value.password))).fetchone()
    return session_response(user,db,response)

@app.post('/api/auth/login')
def login(value: Credentials, request: Request, response: Response, db: DB):
    check_origin(request)
    key = hashlib.sha256(((request.client.host if request.client else '')+value.email).encode()).hexdigest()
    if db.execute("SELECT count(*) AS n FROM auth_attempts WHERE fingerprint=%s AND created_at>now()-interval '15 minutes'",(key,)).fetchone()['n']>=10: fail(429,'Demasiados intentos. Espera 15 minutos.')
    db.execute('INSERT INTO auth_attempts(fingerprint) VALUES(%s)',(key,)); db.commit()
    user = db.execute('SELECT * FROM users WHERE email=%s',(value.email,)).fetchone()
    # Igualar el trabajo de hash para correos inexistentes.
    valid = password_matches(value.password,user['password_hash'] if user else '0'*32+':'+'0'*64)
    if not user or not valid: fail(401,'Correo o contraseña incorrectos.')
    db.execute('DELETE FROM auth_attempts WHERE fingerprint=%s',(key,))
    return session_response(user,db,response)

@app.get('/api/auth/session')
def session(request: Request, db: DB):
    u = optional_user(request,db)
    return {'user':{k:u[k] for k in ('id','name','email','role')} if u else None,'csrf':u['csrf'] if u else None}

@app.post('/api/auth/logout',status_code=204)
def logout(request: Request,response: Response, db: DB):
    require_user(request,db)
    token = request.cookies.get(COOKIE,'')
    db.execute('DELETE FROM sessions WHERE token_hash=%s',(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(COOKIE,path='/')

@app.get('/api/health')
def health(db: DB):
    db.execute('SELECT 1')
    return {'status':'ok','service':'Bagstore integrada','database':'PostgreSQL','version':'1.0.0'}

State = Literal['activo','inactivo']
class ImageInput(Input):
    url: str = Field(max_length=500)
    texto_alternativo: str | None = Field(default=None,max_length=150)
    orden: int = Field(default=0,ge=0)
    es_principal: bool = False
    @field_validator('url')
    @classmethod
    def url_ok(cls,v):
        if not re.match(r'^https?://[^\s]+$',v): raise ValueError('Usa una URL HTTP o HTTPS.')
        return v
class CategoryInput(Input):
    nombre: str = Field(min_length=2,max_length=80)
    descripcion: str | None = Field(default=None,max_length=1000)
    orden: int = Field(default=0,ge=0)
    estado: State = 'activo'
class ColorInput(Input):
    nombre: str = Field(min_length=2,max_length=40)
    tono: str = Field(pattern=r'^#[0-9a-fA-F]{6}$')
class ProductInput(Input):
    nombre: str = Field(min_length=2,max_length=150)
    descripcion: str | None = Field(default=None,max_length=5000)
    precio: Decimal = Field(gt=0,le=999999.99,max_digits=8,decimal_places=2)
    sku: str | None = Field(default=None,min_length=3,max_length=50,pattern=r'^[A-Z0-9]+(?:-[A-Z0-9]+)*$')
    categoria_id: int = Field(gt=0)
    color_id: int | None = Field(default=None,gt=0)
    existencias: int = Field(ge=0,le=1000000)
    imagenes: list[ImageInput] = Field(default_factory=list,max_length=10)
    estado: State = 'activo'
class CollectionInput(Input):
    nombre: str = Field(min_length=2,max_length=100)
    descripcion: str | None = Field(default=None,max_length=2000)
    imagen_portada_url: str | None = Field(default=None,max_length=500)
    estado: State = 'activo'
    producto_ids: list[int] = Field(default_factory=list,max_length=200)

def get_row(db,table,id,lock=False):
    assert table in {'products','categories','collections','orders','returns'}
    row = db.execute(f'SELECT * FROM {table} WHERE id=%s'+(' FOR UPDATE' if lock else ''),(id,)).fetchone()
    if not row: fail(404,'No encontramos el registro.')
    return row
def category_view(db,r):
    return {**r,'creado_en':r['created_at'],'actualizado_en':r['updated_at'],'total_productos':db.execute('SELECT count(*) AS n FROM products WHERE categoria_id=%s AND NOT deleted',(r['id'],)).fetchone()['n']}
def collection_view(db,r,admin):
    ids = [p['product_id'] for p in db.execute('SELECT cp.product_id FROM collection_products cp JOIN products p ON p.id=cp.product_id WHERE cp.collection_id=%s AND NOT p.deleted'+('' if admin else " AND p.estado='activo'"),(r['id'],)).fetchall()]
    return {**r,'creado_en':r['created_at'],'actualizado_en':r['updated_at'],'total_productos':len(ids),**({'producto_ids':ids} if admin else {})}
def product_view(db,r,detail=False,admin=False):
    cat = get_row(db,'categories',r['categoria_id'])
    col = db.execute('SELECT id,nombre,tono FROM colors WHERE id=%s',(r['color_id'],)).fetchone() if r['color_id'] else None
    base = {'id':r['id'],'nombre':r['nombre'],'slug':r['slug'],'precio':float(r['precio']),'disponible':r['existencias']>0,'estado':r['estado'],'categoria':{k:cat[k] for k in ('id','nombre','slug')},'color':col,'imagen_principal':next((i for i in r['imagenes'] if i['es_principal']),r['imagenes'][0] if r['imagenes'] else None)}
    if detail:
        cols = db.execute('SELECT c.id,c.nombre,c.slug FROM collections c JOIN collection_products cp ON cp.collection_id=c.id WHERE cp.product_id=%s'+('' if admin else " AND c.estado='activo'"),(r['id'],)).fetchall()
        base.update(descripcion=r['descripcion'],sku=r['sku'],existencias=r['existencias'],imagenes=r['imagenes'],colecciones=cols,creado_en=r['created_at'],actualizado_en=r['updated_at'])
    return base
def paginated(rows,pagina,por_pagina):
    total=len(rows)
    return {'datos':rows[(pagina-1)*por_pagina:pagina*por_pagina],'paginacion':{'pagina':pagina,'por_pagina':por_pagina,'total':total,'total_paginas':(total+por_pagina-1)//por_pagina}}

@app.get('/api/colores')
def colors(db: DB): return {'datos':db.execute('SELECT id,nombre,tono FROM colors ORDER BY id').fetchall()}
@app.post('/api/colores',status_code=201)
def create_color(v: ColorInput,request: Request,db: DB):
    require_user(request,db,True)
    if db.execute('SELECT id FROM colors WHERE normalized=%s',(norm(v.nombre),)).fetchone(): fail(409,'Ya existe este color.','nombre')
    return db.execute('INSERT INTO colors(nombre,normalized,tono) VALUES(%s,%s,%s) RETURNING id,nombre,tono',(v.nombre,norm(v.nombre),v.tono)).fetchone()

@app.get('/api/productos')
def products(request: Request,db: DB,pagina:int=1,por_pagina:int=20,nombre:str='',categoria_id:int|None=None,categoria:str|None=None,coleccion_id:int|None=None,coleccion:str|None=None,color_id:int|None=None,disponible:bool|None=None,estado:Literal['activo','inactivo','todos']='activo',orden:str='reciente'):
    if pagina<1 or not 1<=por_pagina<=100: fail(422,'Paginación inválida.')
    admin=is_admin(request,db)
    if estado!='activo' and not admin: fail(403,'Necesitas acceso administrativo para consultar inactivos.')
    rows=db.execute('SELECT * FROM products WHERE NOT deleted ORDER BY id DESC').fetchall()
    if categoria: categoria_id=(db.execute('SELECT id FROM categories WHERE slug=%s',(categoria,)).fetchone() or {'id':-1})['id']
    if coleccion: coleccion_id=(db.execute('SELECT id FROM collections WHERE slug=%s',(coleccion,)).fetchone() or {'id':-1})['id']
    members={r['product_id'] for r in db.execute('SELECT product_id FROM collection_products WHERE collection_id=%s',(coleccion_id,)).fetchall()} if coleccion_id is not None else None
    rows=[r for r in rows if (estado=='todos' or r['estado']==estado) and (not categoria_id or r['categoria_id']==categoria_id) and (not color_id or r['color_id']==color_id) and (disponible is None or (r['existencias']>0)==disponible) and norm(nombre) in norm(r['nombre']) and (members is None or r['id'] in members)]
    if not admin: rows=[r for r in rows if get_row(db,'categories',r['categoria_id'])['estado']=='activo']
    if orden in ('nombre_asc','nombre_desc'): rows.sort(key=lambda r:r['nombre'].lower(),reverse=orden.endswith('desc'))
    elif orden in ('precio_asc','precio_desc'): rows.sort(key=lambda r:r['precio'],reverse=orden.endswith('desc'))
    elif orden!='reciente': fail(422,'Orden inválido.')
    return paginated([product_view(db,r,admin=admin) for r in rows],pagina,por_pagina)

@app.get('/api/productos/{id}')
def product(id:int,request: Request,db: DB):
    r=get_row(db,'products',id);admin=is_admin(request,db)
    if r['deleted'] or (not admin and (r['estado']!='activo' or get_row(db,'categories',r['categoria_id'])['estado']!='activo')): fail(404,'Este producto no está disponible.')
    return product_view(db,r,True,admin)

def save_product(v,id,request,db):
    user=require_user(request,db,True)
    category=get_row(db,'categories',v.categoria_id)
    if category['estado']!='activo' and v.estado=='activo': fail(422,'La categoría está inactiva.','categoria_id')
    if v.color_id and not db.execute('SELECT 1 FROM colors WHERE id=%s',(v.color_id,)).fetchone(): fail(422,'Color inválido.','color_id')
    images=[i.model_dump() for i in v.imagenes]
    if len({i['orden'] for i in images})!=len(images) or sum(i['es_principal'] for i in images)>1: fail(422,'Revisa el orden y la imagen principal.','imagenes')
    if images and not any(i['es_principal'] for i in images): images[0]['es_principal']=True
    if id:
        old=get_row(db,'products',id,True)
        if old['deleted']: fail(404,'Producto eliminado.')
        if v.sku and v.sku!=old['sku']: fail(422,'El SKU no puede cambiarse.','sku')
        r=db.execute('UPDATE products SET nombre=%s,descripcion=%s,precio=%s,categoria_id=%s,color_id=%s,existencias=%s,imagenes=%s,estado=%s,updated_at=now() WHERE id=%s RETURNING *',(v.nombre,v.descripcion,v.precio,v.categoria_id,v.color_id,v.existencias,Jsonb(images),v.estado,id)).fetchone()
        if old['existencias']!=v.existencias: db.execute('INSERT INTO stock_movements(product_id,user_id,before_qty,after_qty,reason) VALUES(%s,%s,%s,%s,%s)',(id,user['id'],old['existencias'],v.existencias,'Edición de producto'))
    else:
        if not v.sku: fail(422,'El SKU es obligatorio.','sku')
        if db.execute('SELECT id FROM products WHERE sku=%s',(v.sku,)).fetchone(): fail(409,'Este SKU ya existe.','sku')
        r=db.execute('INSERT INTO products(nombre,slug,descripcion,precio,sku,categoria_id,color_id,existencias,imagenes,estado) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',(v.nombre,slug(v.nombre)+'-'+secrets.token_hex(3),v.descripcion,v.precio,v.sku,v.categoria_id,v.color_id,v.existencias,Jsonb(images),v.estado)).fetchone()
    return product_view(db,r,True,True)
@app.post('/api/productos',status_code=201)
def create_product(v:ProductInput,request:Request,db:DB): return save_product(v,None,request,db)
@app.put('/api/productos/{id}')
def update_product(id:int,v:ProductInput,request:Request,db:DB): return save_product(v,id,request,db)
@app.delete('/api/productos/{id}',status_code=204)
def delete_product(id:int,request:Request,db:DB):
    require_user(request,db,True);get_row(db,'products',id,True)
    db.execute("UPDATE products SET deleted=true,estado='inactivo',updated_at=now() WHERE id=%s",(id,));db.execute('DELETE FROM collection_products WHERE product_id=%s',(id,))

@app.get('/api/categorias')
def categories(request:Request,db:DB,pagina:int=1,por_pagina:int=20,estado:Literal['activo','inactivo','todos']='activo'):
    if pagina<1 or not 1<=por_pagina<=100: fail(422,'Paginación inválida.')
    if estado!='activo' and not is_admin(request,db): fail(403,'Necesitas acceso administrativo.')
    return paginated([category_view(db,r) for r in db.execute('SELECT * FROM categories ORDER BY orden,id').fetchall() if estado=='todos' or r['estado']==estado],pagina,por_pagina)
@app.get('/api/categorias/{id}')
def category(id:int,request:Request,db:DB):
    r=get_row(db,'categories',id)
    if r['estado']!='activo' and not is_admin(request,db):fail(404,'Categoría no disponible.')
    return category_view(db,r)
def save_category(v,id,request,db):
    require_user(request,db,True)
    existing=db.execute('SELECT id FROM categories WHERE normalized=%s AND id<>%s',(norm(v.nombre),id or 0)).fetchone()
    if existing: fail(409,'Ya existe esta categoría.','nombre')
    if id:
        get_row(db,'categories',id)
        r=db.execute('UPDATE categories SET nombre=%s,normalized=%s,descripcion=%s,orden=%s,estado=%s,updated_at=now() WHERE id=%s RETURNING *',(v.nombre,norm(v.nombre),v.descripcion,v.orden,v.estado,id)).fetchone()
    else:r=db.execute('INSERT INTO categories(nombre,normalized,slug,descripcion,orden,estado) VALUES(%s,%s,%s,%s,%s,%s) RETURNING *',(v.nombre,norm(v.nombre),slug(v.nombre)+'-'+secrets.token_hex(3),v.descripcion,v.orden,v.estado)).fetchone()
    return category_view(db,r)
@app.post('/api/categorias',status_code=201)
def create_category(v:CategoryInput,request:Request,db:DB):return save_category(v,None,request,db)
@app.put('/api/categorias/{id}')
def update_category(id:int,v:CategoryInput,request:Request,db:DB):return save_category(v,id,request,db)
@app.delete('/api/categorias/{id}',status_code=204)
def delete_category(id:int,request:Request,db:DB):
    require_user(request,db,True);get_row(db,'categories',id)
    if db.execute('SELECT 1 FROM products WHERE categoria_id=%s',(id,)).fetchone(): fail(409,'La categoría tiene productos asociados.')
    db.execute('DELETE FROM categories WHERE id=%s',(id,))

@app.get('/api/colecciones')
def collections(request:Request,db:DB,pagina:int=1,por_pagina:int=20,estado:Literal['activo','inactivo','todos']='activo'):
    if pagina<1 or not 1<=por_pagina<=100:fail(422,'Paginación inválida.')
    admin=is_admin(request,db)
    if estado!='activo' and not admin:fail(403,'Necesitas acceso administrativo.')
    return paginated([collection_view(db,r,admin) for r in db.execute('SELECT * FROM collections ORDER BY id').fetchall() if estado=='todos' or r['estado']==estado],pagina,por_pagina)
@app.get('/api/colecciones/{id}')
def collection(id:int,request:Request,db:DB):
    r=get_row(db,'collections',id);admin=is_admin(request,db)
    if r['estado']!='activo' and not admin:fail(404,'Colección no disponible.')
    return collection_view(db,r,admin)
def save_collection(v,id,request,db):
    require_user(request,db,True)
    if v.imagen_portada_url and not re.match(r'^https?://[^\s]+$',v.imagen_portada_url):fail(422,'Portada inválida.','imagen_portada_url')
    if len(set(v.producto_ids))!=len(v.producto_ids):fail(422,'Hay productos duplicados.','producto_ids')
    for pid in v.producto_ids:
        if pid<=0 or get_row(db,'products',pid)['deleted']:fail(422,'Producto no válido.','producto_ids')
    if db.execute('SELECT 1 FROM collections WHERE normalized=%s AND id<>%s',(norm(v.nombre),id or 0)).fetchone():fail(409,'Ya existe esta colección.','nombre')
    if id:
        get_row(db,'collections',id)
        r=db.execute('UPDATE collections SET nombre=%s,normalized=%s,descripcion=%s,imagen_portada_url=%s,estado=%s,updated_at=now() WHERE id=%s RETURNING *',(v.nombre,norm(v.nombre),v.descripcion,v.imagen_portada_url,v.estado,id)).fetchone()
    else:r=db.execute('INSERT INTO collections(nombre,normalized,slug,descripcion,imagen_portada_url,estado) VALUES(%s,%s,%s,%s,%s,%s) RETURNING *',(v.nombre,norm(v.nombre),slug(v.nombre)+'-'+secrets.token_hex(3),v.descripcion,v.imagen_portada_url,v.estado)).fetchone()
    db.execute('DELETE FROM collection_products WHERE collection_id=%s',(r['id'],))
    for pid in v.producto_ids:db.execute('INSERT INTO collection_products VALUES(%s,%s)',(r['id'],pid))
    return collection_view(db,r,True)
@app.post('/api/colecciones',status_code=201)
def create_collection(v:CollectionInput,request:Request,db:DB):return save_collection(v,None,request,db)
@app.put('/api/colecciones/{id}')
def update_collection(id:int,v:CollectionInput,request:Request,db:DB):return save_collection(v,id,request,db)
@app.delete('/api/colecciones/{id}',status_code=204)
def delete_collection(id:int,request:Request,db:DB):require_user(request,db,True);get_row(db,'collections',id);db.execute('DELETE FROM collections WHERE id=%s',(id,))

@app.post('/api/uploads',status_code=201)
def upload(file:UploadFile,request:Request,db:DB):
    require_user(request,db,True)
    raw=file.file.read(5*1024*1024+1)
    if len(raw)>5*1024*1024:fail(422,'La foto no puede superar 5 MB.')
    try:
        image=Image.open(io.BytesIO(raw))
        if image.format not in ('JPEG','PNG','WEBP') or image.width*image.height>25000000:fail(422,'Usa JPG, PNG o WebP de hasta 25 megapíxeles.')
        image.load();image.thumbnail((1600,1600));image=image.convert('RGB')
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError):fail(422,'No pudimos leer la imagen.')
    name=secrets.token_hex(20)+'.jpg';image.save(UPLOADS/name,'JPEG',quality=88)
    origin=request.headers.get('origin') or os.environ.get('PUBLIC_ORIGIN') or config().get('public_origin','http://127.0.0.1:5173')
    return {'url':origin+'/api/media/'+name,'texto_alternativo':None,'orden':0,'es_principal':False}

class StockInput(Input): quantity:int=Field(ge=0,le=1000000); reason:str=Field(min_length=3,max_length=200)
@app.get('/api/inventario')
def stock_list(request:Request,db:DB):
    require_user(request,db,True)
    return {'datos':db.execute('SELECT id,nombre,sku,existencias,estado FROM products WHERE NOT deleted ORDER BY id LIMIT 500').fetchall()}
@app.put('/api/inventario/{id}')
def adjust_stock(id:int,v:StockInput,request:Request,db:DB):
    user=require_user(request,db,True);p=get_row(db,'products',id,True)
    db.execute('UPDATE products SET existencias=%s,updated_at=now() WHERE id=%s',(v.quantity,id))
    db.execute('INSERT INTO stock_movements(product_id,user_id,before_qty,after_qty,reason) VALUES(%s,%s,%s,%s,%s)',(id,user['id'],p['existencias'],v.quantity,v.reason))
    return product_view(db,get_row(db,'products',id),True,True)
@app.get('/api/inventario/movimientos')
def stock_history(request:Request,db:DB):
    require_user(request,db,True)
    return {'datos':db.execute('SELECT m.*,p.nombre FROM stock_movements m JOIN products p ON p.id=m.product_id ORDER BY m.id DESC LIMIT 100').fetchall()}

class Line(Input): id:int=Field(gt=0); qty:int=Field(ge=1,le=10)
class Address(Input):
    name:str=Field(min_length=2,max_length=100)
    phone:str=Field(pattern=r'^[0-9+ ()-]{7,25}$')
    street:str=Field(min_length=5,max_length=200)
    city:str=Field(min_length=2,max_length=100)
    region:str=Field(min_length=2,max_length=100)
    postcode:str=Field(pattern=r'^\d{5}$')
class OrderInput(Input):
    lines:list[Line]=Field(min_length=1,max_length=100)
    delivery:Literal['pickup','shipping']
    payment:Literal['transferencia','efectivo']='transferencia'
    coupon:str=Field(default='',max_length=30)
    gift:bool=False
    address:Address|None=None
    idempotency_key:str=Field(min_length=10,max_length=100)

@app.post('/api/checkout/quote')
def quote_order(v:OrderInput,request:Request,db:DB):
    require_user(request,db)
    if v.delivery=='shipping' and not v.address:fail(422,'Completa el domicilio de entrega.')
    if v.coupon and v.coupon.upper()!='BEIGE10':fail(422,'Cupón no válido.','coupon')
    if len({l.id for l in v.lines})!=len(v.lines):fail(422,'No repitas productos.')
    subtotal=Decimal(0)
    for l in v.lines:
        p=get_row(db,'products',l.id)
        if p['deleted'] or p['estado']!='activo' or get_row(db,'categories',p['categoria_id'])['estado']!='activo' or p['existencias']<l.qty:fail(409,'Revisa la disponibilidad de tu carrito.')
        subtotal+=p['precio']*l.qty
    subtotal=money(subtotal);discount=money(subtotal*Decimal('.1')) if v.coupon else Decimal(0);shipping=money(os.environ.get('SHIPPING_PRICE','79')) if v.delivery=='shipping' else Decimal(0)
    return {'subtotal':float(subtotal),'discount':float(discount),'shipping':float(shipping),'total':float(subtotal-discount+shipping)}

def order_view(db,r):
    items=db.execute('SELECT product_id AS "productId",nombre AS name,sku,color,quantity AS qty,price FROM order_items WHERE order_id=%s ORDER BY id',(r['id'],)).fetchall()
    return {'id':str(r['id']),'date':r['created_at'].isoformat(),'items':[{**i,'price':float(i['price'])} for i in items],'subtotal':float(r['subtotal']),'discount':float(r['discount']),'shipping':float(r['shipping']),'total':float(r['total']),'delivery':'Recoger en tienda' if r['delivery']=='pickup' else 'Envío a domicilio','payment':r['payment'],'payment_status':r['payment_status'],'status':r['status'],'gift':r['gift'],'address':r['address'],'carrier':r['carrier'],'tracking':r['tracking'],'customer':db.execute('SELECT name,email FROM users WHERE id=%s',(r['user_id'],)).fetchone()}

@app.post('/api/pedidos',status_code=201)
def create_order(v:OrderInput,request:Request,db:DB):
    user=require_user(request,db)
    if v.delivery=='shipping' and not v.address:fail(422,'Completa el domicilio de entrega.','address')
    if v.payment=='efectivo' and v.delivery!='pickup':fail(422,'El efectivo está disponible solo al recoger en tienda.','payment')
    if len({l.id for l in v.lines})!=len(v.lines):fail(422,'No repitas productos en el pedido.')
    if v.coupon and v.coupon.upper()!='BEIGE10':fail(422,'Cupón no válido.','coupon')
    payload_hash=hashlib.sha256(json.dumps(v.model_dump(mode='json'),sort_keys=True).encode()).hexdigest()
    db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(str(user['id'])+v.idempotency_key,))
    existing=db.execute('SELECT * FROM orders WHERE user_id=%s AND idempotency_key=%s',(user['id'],v.idempotency_key)).fetchone()
    if existing:
        if existing['request_hash']!=payload_hash:fail(409,'La solicitud de compra cambió. Revisa tu carrito.')
        return order_view(db,existing)
    lines=[]
    for l in sorted(v.lines,key=lambda l:l.id):
        p=get_row(db,'products',l.id,True)
        if p['deleted'] or p['estado']!='activo' or get_row(db,'categories',p['categoria_id'])['estado']!='activo' or l.qty>p['existencias']:fail(409,'Un producto no tiene disponibilidad suficiente. Revisa el carrito.')
        lines.append((p,l.qty))
    subtotal=money(sum((p['precio']*qty for p,qty in lines),Decimal(0)));discount=money(subtotal*Decimal('.10')) if v.coupon else Decimal(0)
    shipping=money(os.environ.get('SHIPPING_PRICE','79')) if v.delivery=='shipping' else Decimal(0)
    if shipping<0:fail(500,'Tarifa de envío no configurada correctamente.')
    r=db.execute('INSERT INTO orders(user_id,idempotency_key,request_hash,subtotal,discount,shipping,total,delivery,payment,gift,address) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',(user['id'],v.idempotency_key,payload_hash,subtotal,discount,shipping,subtotal-discount+shipping,v.delivery,v.payment,v.gift,Jsonb(v.address.model_dump() if v.address else {}))).fetchone()
    for p,qty in lines:
        color=db.execute('SELECT nombre FROM colors WHERE id=%s',(p['color_id'],)).fetchone() if p['color_id'] else None
        db.execute('INSERT INTO order_items(order_id,product_id,nombre,sku,color,quantity,price) VALUES(%s,%s,%s,%s,%s,%s,%s)',(r['id'],p['id'],p['nombre'],p['sku'],color['nombre'] if color else None,qty,p['precio']))
        db.execute('UPDATE products SET existencias=existencias-%s,updated_at=now() WHERE id=%s',(qty,p['id']))
        db.execute('INSERT INTO stock_movements(product_id,user_id,before_qty,after_qty,reason) VALUES(%s,%s,%s,%s,%s)',(p['id'],user['id'],p['existencias'],p['existencias']-qty,'Pedido '+str(r['id'])))
    return order_view(db,r)

@app.get('/api/pedidos')
def orders(request:Request,db:DB,desde:date|None=None,hasta:date|None=None):
    user=require_user(request,db)
    if desde and hasta and desde>hasta:fail(422,'La fecha inicial no puede superar la final.')
    rows=db.execute('SELECT * FROM orders WHERE (%s OR user_id=%s) AND (%s::date IS NULL OR created_at::date>=%s::date) AND (%s::date IS NULL OR created_at::date<=%s::date) ORDER BY id DESC LIMIT 500',(user['role']=='administrador',user['id'],desde,desde,hasta,hasta)).fetchall()
    return {'datos':[order_view(db,r) for r in rows]}
@app.get('/api/pedidos/{id}')
def order_detail(id:int,request:Request,db:DB):
    user=require_user(request,db);r=get_row(db,'orders',id)
    if r['user_id']!=user['id'] and user['role']!='administrador':fail(404,'Pedido no disponible.')
    return order_view(db,r)
class OrderUpdate(Input):
    status:Literal['pendiente','preparando','listo','enviado','entregado']
    carrier:str|None=Field(default=None,max_length=80)
    tracking:str|None=Field(default=None,max_length=100)
    confirm_payment:bool=False
@app.put('/api/pedidos/{id}')
def order_update(id:int,v:OrderUpdate,request:Request,db:DB):
    user=require_user(request,db,True);r=get_row(db,'orders',id,True)
    transitions={'pendiente':{'pendiente','preparando'},'preparando':{'preparando','listo','enviado'},'listo':{'listo','entregado'},'enviado':{'enviado','entregado'},'entregado':{'entregado'}}
    if v.status not in transitions[r['status']]:fail(422,'El estado no puede avanzar de esa forma.')
    paid=v.confirm_payment or r['payment_status']=='confirmado'
    if v.status in ('enviado','entregado') and not paid:fail(422,'Confirma el pago verificado antes de entregar o enviar.')
    if v.status=='enviado' and (r['delivery']!='shipping' or not v.carrier or not v.tracking):fail(422,'Indica la paquetería y la guía para enviar a domicilio.')
    if v.status=='listo' and r['delivery']!='pickup':fail(422,'Listo para recoger solo corresponde a recogida en tienda.')
    db.execute('UPDATE orders SET status=%s,carrier=%s,tracking=%s,payment_status=%s WHERE id=%s',(v.status,v.carrier,v.tracking,'confirmado' if paid else 'pendiente',id))
    db.execute('INSERT INTO order_events(order_id,user_id,action) VALUES(%s,%s,%s)',(id,user['id'],json.dumps(v.model_dump())))
    return order_view(db,get_row(db,'orders',id))

class ReviewInput(Input):rating:int=Field(ge=1,le=5);comment:str=Field(min_length=5,max_length=1000)
@app.get('/api/productos/{id}/resenas')
def reviews(id:int,request:Request,db:DB):
    product(id,request,db)
    return {'datos':db.execute('SELECT r.id,r.rating,r.comment,r.created_at AS date,u.name FROM reviews r JOIN users u ON u.id=r.user_id WHERE product_id=%s ORDER BY r.id DESC',(id,)).fetchall()}
@app.post('/api/productos/{id}/resenas',status_code=201)
def create_review(id:int,v:ReviewInput,request:Request,db:DB):
    u=require_user(request,db);product(id,request,db)
    db.execute('INSERT INTO reviews(product_id,user_id,rating,comment) VALUES(%s,%s,%s,%s) ON CONFLICT(product_id,user_id) DO UPDATE SET rating=excluded.rating,comment=excluded.comment,created_at=now()',(id,u['id'],v.rating,v.comment))
    return {'ok':True}
class ReturnInput(Input):order_id:int=Field(gt=0);product_id:int=Field(gt=0);reason:str=Field(min_length=2,max_length=80);comment:str=Field(min_length=5,max_length=1000)
@app.get('/api/devoluciones')
def returns(request:Request,db:DB):
    u=require_user(request,db)
    return {'datos':db.execute('SELECT r.*,oi.nombre AS product_name FROM returns r JOIN order_items oi ON oi.order_id=r.order_id AND oi.product_id=r.product_id WHERE (%s OR r.user_id=%s) ORDER BY r.id DESC',(u['role']=='administrador',u['id'])).fetchall()}
@app.post('/api/devoluciones',status_code=201)
def create_return(v:ReturnInput,request:Request,db:DB):
    u=require_user(request,db);r=get_row(db,'orders',v.order_id,True)
    if r['user_id']!=u['id']:fail(404,'Pedido no disponible.')
    if r['status']!='entregado':fail(422,'Solo puedes solicitar devolución de un pedido entregado.')
    if not db.execute('SELECT 1 FROM order_items WHERE order_id=%s AND product_id=%s',(v.order_id,v.product_id)).fetchone():fail(422,'Este producto no pertenece al pedido.')
    return db.execute('INSERT INTO returns(order_id,product_id,user_id,reason,comment) VALUES(%s,%s,%s,%s,%s) RETURNING *',(v.order_id,v.product_id,u['id'],v.reason,v.comment)).fetchone()
class ReturnUpdate(Input):status:Literal['En revisión','Resuelta','Rechazada']
@app.put('/api/devoluciones/{id}')
def update_return(id:int,v:ReturnUpdate,request:Request,db:DB):
    require_user(request,db,True);r=get_row(db,'returns',id,True)
    if r['status'] in ('Resuelta','Rechazada') and r['status']!=v.status:fail(409,'Esta solicitud ya está cerrada.')
    return db.execute('UPDATE returns SET status=%s WHERE id=%s RETURNING *',(v.status,id)).fetchone()

# También permite servir la compilación del frontend desde Python, sin Vite.
DIST=ROOT.parent/'dist'
if DIST.exists():app.mount('/',StaticFiles(directory=DIST,html=True),name='frontend')
