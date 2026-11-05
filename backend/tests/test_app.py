import concurrent.futures
import io
import json
import os
import secrets
import sys
from pathlib import Path

import psycopg
from psycopg import sql
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from server import app,connect,UPLOADS

def register():
    c=TestClient(app)
    r=c.post('/api/auth/register',json={'name':'Cliente de pruebas','email':secrets.token_hex(8)+'@example.test','password':'Cliente-test-123'})
    assert r.status_code==201,r.text
    c.headers['X-CSRF-Token']=r.json()['csrf']
    return c
def admin():
    c=TestClient(app);r=c.post('/api/auth/login',json={'email':'admin@example.test','password':'Test-admin-123456'})
    assert r.status_code==200,r.text
    c.headers['X-CSRF-Token']=r.json()['csrf'];return c
def draft(**kwargs): return {'nombre':'Producto '+secrets.token_hex(4),'precio':100.15,'sku':'TEST-'+secrets.token_hex(6).upper(),'categoria_id':1,'color_id':3,'existencias':10,'imagenes':[],'estado':'activo',**kwargs}
def product(c,**kwargs):
    value=draft(**kwargs);r=c.post('/api/productos',json=value);assert r.status_code==201,r.text;return r.json(),value
def order_payload(id,**kwargs):return {'lines':[{'id':id,'qty':1}],'delivery':'pickup','payment':'efectivo','idempotency_key':secrets.token_hex(16),**kwargs}

def test_auth_permissions_csrf_and_cookie():
    c=register();data=c.get('/api/auth/session').json();assert data['user']['role']=='cliente'
    assert c.post('/api/productos',json=draft()).status_code==403
    assert c.cookies.get('bagstore_session')
    assert 'password' not in str(data)
    token=c.headers.pop('X-CSRF-Token');assert c.post('/api/auth/logout').status_code==403
    c.headers['X-CSRF-Token']=token;assert c.post('/api/auth/logout').status_code==204
    assert c.get('/api/auth/session').json()['user'] is None
    assert TestClient(app).get('/api/pedidos').status_code==401

def test_normalized_colors_admin_writes_and_inactive_read():
    a=admin();assert a.post('/api/colores',json={'nombre':'  ROJÓ  ','tono':'#FF0000'}).status_code==409
    p,v=product(a);v['estado']='inactivo';assert a.put(f"/api/productos/{p['id']}",json=v).status_code==200
    assert TestClient(app).get(f"/api/productos/{p['id']}").status_code==404
    assert a.get(f"/api/productos/{p['id']}").status_code==200
    v['estado']='activo';assert a.put(f"/api/productos/{p['id']}",json=v).status_code==200
    assert TestClient(app).get('/api/productos?estado=todos').status_code==403
    assert a.get('/api/productos?estado=todos').status_code==200

def test_collection_membership_and_category_dependency():
    a=admin();p,v=product(a,estado='inactivo')
    payload={'nombre':'Colección '+secrets.token_hex(4),'estado':'activo','producto_ids':[1,p['id']]}
    r=a.post('/api/colecciones',json=payload);assert r.status_code==201,r.text;cid=r.json()['id']
    assert set(a.get(f'/api/colecciones/{cid}').json()['producto_ids'])=={1,p['id']}
    assert 'producto_ids' not in TestClient(app).get(f'/api/colecciones/{cid}').json()
    assert a.delete('/api/categorias/1').status_code==409

def test_order_atomic_totals_idempotency_and_ownership():
    a=admin();p,v=product(a);c=register();payload=order_payload(p['id'],lines=[{'id':p['id'],'qty':3}],coupon='BEIGE10')
    r=c.post('/api/pedidos',json=payload);assert r.status_code==201,r.text;o=r.json()
    assert o['subtotal']==300.45 and o['discount']==30.05 and o['total']==270.4
    assert o['payment_status']=='pendiente'
    assert c.post('/api/pedidos',json=payload).json()['id']==o['id']
    assert a.get(f"/api/productos/{p['id']}").json()['existencias']==7
    assert register().get('/api/pedidos/'+o['id']).status_code==404
    assert c.post('/api/pedidos',json={**payload,'lines':[{'id':p['id'],'qty':1}]}).status_code==409
    assert c.post('/api/pedidos',json={**order_payload(p['id']),'total':1}).status_code==422

def test_concurrent_last_unit_cannot_be_sold_twice():
    a=admin();p,_=product(a,existencias=1);one,two=register(),register()
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda c:c.post('/api/pedidos',json=order_payload(p['id'])).status_code,[one,two]))
    assert sorted(results)==[201,409],results
    assert a.get(f"/api/productos/{p['id']}").json()['existencias']==0

def test_manual_payment_delivery_returns_and_reviews():
    a=admin();p,_=product(a);c=register();o=c.post('/api/pedidos',json=order_payload(p['id'])).json();oid=o['id']
    assert c.post('/api/devoluciones',json={'order_id':int(oid),'product_id':p['id'],'reason':'Cambio','comment':'Quiero cambiar este producto'}).status_code==422
    assert a.put('/api/pedidos/'+oid,json={'status':'preparando'}).status_code==200
    assert a.put('/api/pedidos/'+oid,json={'status':'listo'}).status_code==200
    assert a.put('/api/pedidos/'+oid,json={'status':'entregado'}).status_code==422
    assert a.put('/api/pedidos/'+oid,json={'status':'entregado','confirm_payment':True}).status_code==200
    r=c.post('/api/devoluciones',json={'order_id':int(oid),'product_id':p['id'],'reason':'Cambio','comment':'Quiero cambiar este producto'});assert r.status_code==201,r.text
    assert c.post('/api/devoluciones',json={'order_id':int(oid),'product_id':p['id'],'reason':'Cambio','comment':'Otra solicitud igual'}).status_code==409
    assert a.put('/api/devoluciones/'+str(r.json()['id']),json={'status':'En revisión'}).status_code==200
    assert c.post(f"/api/productos/{p['id']}/resenas",json={'rating':5,'comment':'Una bolsa muy práctica'}).status_code==201
    assert TestClient(app).get(f"/api/productos/{p['id']}/resenas").json()['datos'][0]['rating']==5

def test_shipping_requires_address_and_stock_history():
    a=admin();p,_=product(a);c=register()
    assert c.post('/api/pedidos',json=order_payload(p['id'],delivery='shipping',payment='transferencia')).status_code==422
    assert a.put(f"/api/inventario/{p['id']}",json={'quantity':2,'reason':'Conteo de prueba'}).status_code==200
    assert a.get('/api/inventario/movimientos').json()['datos'][0]['after_qty']==2
    assert c.put(f"/api/inventario/{p['id']}",json={'quantity':2,'reason':'No permitido'}).status_code==403

def test_upload_decodes_and_rejects_non_images():
    a=admin();assert a.post('/api/uploads',files={'file':('x.svg',b'<svg/>','image/svg+xml')}).status_code==422
    image=Image.new('RGB',(20,20),'red');buffer=io.BytesIO();image.save(buffer,format='PNG')
    r=a.post('/api/uploads',files={'file':('foto.png',buffer.getvalue(),'image/png')});assert r.status_code==201,r.text
    name=r.json()['url'].rsplit('/',1)[1]
    assert len(name)==44 and name.endswith('.jpg')
    assert (UPLOADS/name).exists();(UPLOADS/name).unlink()

def test_persistence_and_database_constraints():
    c=register();email=c.get('/api/auth/session').json()['user']['email']
    with connect() as db:
        assert db.execute('SELECT count(*) AS n FROM users WHERE email=%s',(email,)).fetchone()['n']==1
        hashed=db.execute('SELECT password_hash FROM users WHERE email=%s',(email,)).fetchone()['password_hash'];assert 'Cliente-test' not in hashed

def test_quote_shipping_tracking_and_origin_protection():
    a=admin();p,_=product(a);c=register()
    body=order_payload(p['id'],delivery='shipping',payment='transferencia',address={'name':'Persona de prueba','phone':'5555555555','street':'Domicilio de pruebas 123','city':'Ciudad de pruebas','region':'Estado de pruebas','postcode':'00000'},coupon='BEIGE10')
    quote=c.post('/api/checkout/quote',json=body);assert quote.status_code==200,quote.text
    assert quote.json()['total']==169.13
    order=c.post('/api/pedidos',json=body);assert order.status_code==201,order.text
    o=order.json();assert o['total']==quote.json()['total']
    assert a.put('/api/pedidos/'+o['id'],json={'status':'preparando'}).status_code==200
    assert a.put('/api/pedidos/'+o['id'],json={'status':'enviado','confirm_payment':True}).status_code==422
    assert a.put('/api/pedidos/'+o['id'],json={'status':'enviado','confirm_payment':True,'carrier':'Paquetería de prueba','tracking':'TEST-123'}).status_code==200
    assert c.get('/api/pedidos/'+o['id']).json()['tracking']=='TEST-123'
    assert a.post('/api/colores',headers={'Origin':'https://untrusted.example'},json={'nombre':'No permitido','tono':'#112233'}).status_code==403
    assert TestClient(app).post('/api/auth/register',json={'name':'Prueba','email':'role@example.test','password':'Password-123','role':'administrador'}).status_code==422
