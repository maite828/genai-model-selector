"""Loopback-only prototype. Prompt and generated text are not persisted."""
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
from contextlib import contextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from router import CATALOG, VERSION, WEIGHTS, RouteRequest, route

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'data' / 'decisions.sqlite'
TOKEN = secrets.token_urlsafe(32)
OLLAMA = 'http://127.0.0.1:11434'
LOCAL_BINDINGS = {'local-small': os.getenv('TFM_LOCAL_SMALL', ''),
                  'local-large': os.getenv('TFM_LOCAL_LARGE', '')}
app = FastAPI(title='Selector TFM', version='0.1.0')


@app.middleware('http')
async def local_access(request: Request, call_next):
    host = request.headers.get('host', '').split(':')[0]
    if host not in {'127.0.0.1', 'localhost', 'testserver'}:
        return JSONResponse({'detail': 'Acceso solo local'}, 403)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'} and not secrets.compare_digest(request.headers.get('x-session-token', ''), TOKEN):
        return JSONResponse({'detail': 'Sesion no valida. Recarga la pagina.'}, 403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    response.headers['Cache-Control'] = 'no-store'
    return response


@contextmanager
def database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.execute('CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
            yield conn
    finally:
        conn.close()


def save(result):
    with database() as conn:
        conn.execute('INSERT INTO decisions VALUES (?, ?)', (result['id'], json.dumps(result)))


@app.get('/api/config')
def config():
    return {'token': TOKEN, 'catalog': CATALOG, 'version': VERSION, 'weights': WEIGHTS,
            'bindings': LOCAL_BINDINGS, 'remote_execution': False}


@app.get('/api/health')
def health():
    try:
        with httpx.Client(timeout=2, trust_env=False) as client:
            res = client.get(OLLAMA + '/api/tags')
            res.raise_for_status()
            models = [m['name'] for m in res.json().get('models', [])]
        return {'ollama': True, 'models': models}
    except (httpx.HTTPError, ValueError, KeyError):
        return {'ollama': False, 'models': []}


@app.post('/api/route')
def select_model(request: RouteRequest):
    result = route(request)
    save(result)
    return result


@app.post('/api/execute')
def execute_model(request: RouteRequest):
    # Re-evaluate on the server; never trust a client-supplied model or decision.
    result = route(request)
    selected = result['selected']
    if not selected:
        save(result)
        raise HTTPException(409, 'Abstencion: ningun modelo cumple las restricciones.')
    binding = LOCAL_BINDINGS.get(selected['id'])
    if selected['location'] != 'local' or not binding:
        result['execution'] = {'status': 'blocked', 'reason': 'destination_not_configured'}
        save(result)
        raise HTTPException(409, 'Ejecucion no configurada para este modelo. No se ha enviado la solicitud.')
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=120, trust_env=False) as client:
            tags = client.get(OLLAMA + '/api/tags')
            tags.raise_for_status()
            installed = tags.json().get('models', [])
            model = next((m for m in installed if m.get('name') == binding), None)
            # Fail closed for Ollama cloud-backed models, including locally named aliases.
            if not model or model.get('remote_host') or model.get('remote_model') or 'cloud' in binding.lower():
                raise HTTPException(409, 'El modelo debe estar instalado localmente y no ser un modelo cloud.')
            info = client.post(OLLAMA + '/api/show', json={'model': binding})
            info.raise_for_status()
            if info.json().get('remote_host') or info.json().get('remote_model'):
                raise HTTPException(409, 'Se ha bloqueado un modelo respaldado por la nube.')
            res = client.post(OLLAMA + '/api/generate', json={'model': binding, 'prompt': request.prompt,
                              'stream': False, 'keep_alive': '2m',
                              'options': {'temperature': 0, 'num_ctx': 4096, 'num_predict': request.output_tokens}})
            res.raise_for_status()
            data = res.json()
            if not isinstance(data.get('response'), str) or not data.get('done'):
                raise ValueError('Incomplete response')
    except HTTPException:
        result['execution'] = {'status': 'blocked', 'reason': 'local_model_required', 'model': binding}
        save(result)
        raise
    except (httpx.HTTPError, ValueError, KeyError):
        result['execution'] = {'status': 'failed', 'model': binding}
        save(result)
        raise HTTPException(502, 'Ollama no ha completado la respuesta. Comprueba el servicio y el modelo local.')
    result['execution'] = {'status': 'completed', 'model': binding,
                           'model_digest': model.get('digest'), 'context_tokens': 4096,
                           'done_reason': data.get('done_reason'),
                           'latency_ms': round((time.perf_counter() - started) * 1000),
                           'input_tokens': data.get('prompt_eval_count'), 'output_tokens': data.get('eval_count'),
                           'energy_measured': False}
    save(result)
    return {'decision': result, 'response': data['response']}


@app.get('/api/history')
def history():
    with database() as conn:
        rows = conn.execute('SELECT body FROM decisions ORDER BY rowid DESC LIMIT 100').fetchall()
    return [json.loads(row[0]) for row in rows]


@app.delete('/api/history')
def clear_history():
    with database() as conn:
        conn.execute('DELETE FROM decisions')
    return {'deleted': True}


app.mount('/', StaticFiles(directory=ROOT / 'dist', html=True), name='ui')
