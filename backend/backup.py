"""Copia local de PostgreSQL; no imprime ni coloca contraseñas en argumentos."""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

root=Path(__file__).resolve().parent
cfg=json.loads((root/'.runtime/config.json').read_text(encoding='utf-8'))
url=urlparse(cfg['database_url'])
destination=root/'.runtime/backups'
destination.mkdir(exist_ok=True)
file=destination/('bagstore-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.dump')
pg=Path(os.environ.get('POSTGRES_BIN','C:/Program Files/PostgreSQL/18/bin'))
subprocess.run([str(pg/'pg_dump.exe'),'-h',url.hostname,'-p',str(url.port),'-U',unquote(url.username),'-d',url.path.lstrip('/'),'-Fc','-f',str(file)],env={**os.environ,'PGPASSWORD':unquote(url.password)},check=True)
subprocess.run([str(pg/'pg_restore.exe'),'--list',str(file)],stdout=subprocess.DEVNULL,check=True)
print('Copia verificada: '+str(file))
