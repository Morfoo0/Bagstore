"""Base PostgreSQL privada del proyecto. No modifica servicios ni bases existentes."""
import json
import os
import secrets
import socket
import subprocess
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'

def bootstrap():
    RUNTIME.mkdir(exist_ok=True)
    config_file = RUNTIME / 'config.json'
    if not config_file.exists():
        password = secrets.token_urlsafe(30)
        config = {'database_url':f'postgresql://bagstore:{quote(password)}@127.0.0.1:55432/bagstore', 'pg_password':password, 'admin_email':'admin@bagstore.local', 'admin_password':secrets.token_urlsafe(18), 'public_origin':'http://127.0.0.1:5173'}
        config_file.write_text(json.dumps(config),encoding='utf-8')
        (RUNTIME/'ACCESO-LOCAL.txt').write_text('Acceso administrativo local\nCorreo: '+config['admin_email']+'\nContraseña: '+config['admin_password']+'\nNo publicar este archivo ni reutilizar esta contraseña.\n',encoding='utf-8')
    config = json.loads(config_file.read_text(encoding='utf-8'))
    pg_bin = Path(os.environ.get('POSTGRES_BIN','C:/Program Files/PostgreSQL/18/bin'))
    data = RUNTIME/'postgres'
    if not (data/'PG_VERSION').exists():
        password_file = RUNTIME/'pg-password.tmp'
        password_file.write_text(config['pg_password'],encoding='utf-8')
        try: subprocess.run([str(pg_bin/'initdb.exe'),'-D',str(data),'-U','bagstore','--encoding=UTF8','--locale=C','--auth=scram-sha-256','--pwfile='+str(password_file)],check=True)
        finally: password_file.unlink(missing_ok=True)
    import psycopg
    server = config['database_url'].rsplit('/',1)[0]+'/postgres'
    running=False
    try:
        with psycopg.connect(server,connect_timeout=3) as db:
            directory=db.execute("SELECT current_setting('data_directory')").fetchone()[0]
            if Path(directory).resolve()!=data.resolve():raise RuntimeError('El puerto pertenece a otra base de datos. No se modificó.')
            running=True
    except psycopg.OperationalError:
        try:
            with socket.create_connection(('127.0.0.1',55432),timeout=2):
                raise RuntimeError('El puerto 55432 está ocupado y no se pudo verificar la base. No se intentó iniciar otro servidor.')
        except (ConnectionRefusedError,TimeoutError):pass
    if not running:
        subprocess.run([str(pg_bin/'pg_ctl.exe'),'-D',str(data),'-l',str(RUNTIME/'postgres.log'),'-o','-h 127.0.0.1 -p 55432','-w','start'],check=True)
    with psycopg.connect(server,autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname='bagstore'").fetchone(): conn.execute('CREATE DATABASE bagstore')
    from server import initialize
    initialize()
    print('PostgreSQL de Bagstore disponible en 127.0.0.1:55432. Credenciales administrativas: backend/.runtime/ACCESO-LOCAL.txt')

if __name__ == '__main__': bootstrap()
