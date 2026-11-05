import json
import os
import secrets
import sys
from pathlib import Path
import psycopg
from psycopg import sql
import pytest
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
config=json.loads((ROOT/'.runtime/config.json').read_text())
TEST_DB='bagstore_test_'+secrets.token_hex(5)
server_url=config['database_url'].rsplit('/',1)[0]+'/postgres'
test_url=config['database_url'].rsplit('/',1)[0]+'/'+TEST_DB
os.environ['DATABASE_URL']=test_url
os.environ['BAGSTORE_ADMIN_EMAIL']='admin@example.test'
os.environ['BAGSTORE_ADMIN_PASSWORD']='Test-admin-123456'
from server import app,connect,UPLOADS

@pytest.fixture(scope='session',autouse=True)
def test_database():
    with psycopg.connect(server_url,autocommit=True,connect_timeout=5) as db: db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(TEST_DB)))
    with TestClient(app) as c: assert c.get('/api/health').json()['database']=='PostgreSQL'
    yield
    with psycopg.connect(server_url,autocommit=True,connect_timeout=5) as db: db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(TEST_DB)))
