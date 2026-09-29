"""Start the prototype with the two already-installed pilot models."""
import os
from pathlib import Path
import sys


if __name__ == '__main__':
    os.chdir(Path(__file__).resolve().parent)
    os.environ.setdefault('TFM_LOCAL_SMALL', 'llama3.2:latest')
    os.environ.setdefault('TFM_LOCAL_LARGE', 'qwen2.5:latest')
    os.execv(sys.executable, [sys.executable, '-m', 'uvicorn', 'app:app',
                            '--host', '127.0.0.1', '--port', '8765'])
