import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import httpx

def test_frontend_with_real_postgres_and_http(test_database):
    root=Path(__file__).resolve().parents[2]
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--app-dir',str(root/'backend'),'--host','127.0.0.1','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                if httpx.get(f'http://127.0.0.1:{port}/api/health',timeout=1).status_code==200:break
            except httpx.TransportError:pass
            time.sleep(.2)
        env={**os.environ,'BAGSTORE_TEST_URL':f'http://127.0.0.1:{port}','BAGSTORE_TEST_ADMIN_EMAIL':os.environ['BAGSTORE_ADMIN_EMAIL'],'BAGSTORE_TEST_ADMIN_PASSWORD':os.environ['BAGSTORE_ADMIN_PASSWORD']}
        result=subprocess.run(['node','scripts/check-integrated.mjs'],cwd=root,env=env,capture_output=True,text=True,timeout=90)
        assert result.returncode==0,result.stdout+'\n'+result.stderr
        assert '"erroresDOM":0' in result.stdout
    finally:process.terminate();process.wait(timeout=15)
