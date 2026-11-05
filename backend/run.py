"""Inicia la base privada y mantiene el proceso del backend abierto."""
import subprocess
import sys
from pathlib import Path
from bootstrap import bootstrap

if __name__=='__main__':
    bootstrap()
    try: subprocess.run([sys.executable,'-m','uvicorn','server:app','--app-dir',str(Path(__file__).parent),'--host','127.0.0.1','--port','8001'],check=True)
    except KeyboardInterrupt: pass
