"""Run the frozen pilot locally and prepare independent, model-blind review packets."""
import csv
import hashlib
import json
import platform
import secrets
import shutil
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx

from prepare import validate

ROOT = Path(__file__).resolve().parents[2]
MATERIAL = Path(__file__).resolve().parent
MODELS = ['llama3.2:latest', 'qwen2.5:latest']
OPTIONS = {'num_ctx': 4096, 'num_predict': 512, 'temperature': 0, 'seed': 42}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def git_revision():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def post(client, path, data):
    response = client.post(path, json=data)
    response.raise_for_status()
    return response.json()


def local_model(client, name, expected_digest=None):
    response = client.get('/api/tags')
    response.raise_for_status()
    entry = next(m for m in response.json()['models'] if m['name'] == name)
    info = post(client, '/api/show', {'model': name})
    if any(obj.get(k) for obj in (entry, info) for k in ('remote_host', 'remote_model')) or 'cloud' in name.lower():
        raise RuntimeError('Remote-backed model rejected')
    if expected_digest and entry['digest'] != expected_digest:
        raise RuntimeError('Model digest changed during the run')
    return entry


def packets(out, cases, records):
    by_case = {c['id']: c for c in cases}
    keys = []
    blind = []
    for record in records:
        response_id = 'R-' + uuid4().hex[:12]
        keys.append({'response_id': response_id, 'case_id': record['case_id'],
                     'model': record['model'], 'digest': record['digest'], 'sequence': record['sequence']})
        blind.append({'response_id': response_id, 'case_id': record['case_id'],
                      'status': record['status'], 'truncated': record.get('done_reason') == 'length',
                      'response': record.get('response', '')})
    write_json(out / 'RESTRINGIDO_correspondencia_modelos.json', keys)
    for reviewer in ['Maite', 'Arturo']:
        folder = out / ('evaluacion_' + reviewer)
        folder.mkdir()
        shutil.copyfile(MATERIAL / 'RUBRIC.md', folder / 'RUBRIC.md')
        order = list(blind)
        secrets.SystemRandom().shuffle(order)
        write_json(folder / 'respuestas_anonimas.json', order)
        lines = [f'# Evaluacion independiente: {reviewer}', '',
                 f'Ejecucion: {out.name}. Respuestas: {len(order)}/40.', '',
                 'Completa puntuaciones.csv con ayuda de RUBRIC.md. No consultes la correspondencia de modelos ni los tiempos antes de terminar.', '',
                 'No ejecutes el codigo de las respuestas en tu equipo. Las pruebas funcionales quedan pendientes de un ejecutor aislado.', '']
        for item in order:
            case = by_case[item['case_id']]
            lines.extend([f"## {item['response_id']} | {case['id']} | {case['task']}", '',
                          f"Estado: {item['status']}. Truncada por limite: {item['truncated']}.", '',
                          '### Enunciado', '', case['prompt'], '', '### Respuesta', ''])
            # Indented blocks preserve model output without interpreting Markdown or HTML.
            lines.extend('    ' + s for s in (item['response'] or '[Sin respuesta evaluable]').splitlines())
            lines.extend(['', '### Criterios esperados', ''])
            lines.extend('- ' + s for s in case['expected_points'])
            lines.extend(['', '### Errores criticos', ''])
            lines.extend('- ' + s for s in case['critical_errors'])
            lines.extend(['', '### Formato', ''])
            lines.extend('- ' + s for s in case['format_checks'])
            if 'code_tests' in case:
                lines.extend(['', '### Pruebas de referencia (no ejecutadas)', '',
                              '```json', json.dumps(case['code_tests'], indent=2, ensure_ascii=False), '```'])
            lines.append('')
        (folder / 'CUADERNO.md').write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
        with (folder / 'puntuaciones.csv').open('w', newline='', encoding='utf-8-sig') as stream:
            fields = ['run_id', 'evaluador', 'response_id', 'case_id', 'estado', 'truncada',
                      'correccion_0_3', 'cobertura_0_3', 'instrucciones_0_3', 'claridad_0_3',
                      'errores_criticos', 'evidencia', 'pruebas_codigo_superadas', 'pruebas_codigo_total']
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for item in order:
                writer.writerow({'run_id': out.name, 'evaluador': reviewer, 'response_id': item['response_id'],
                                 'case_id': item['case_id'], 'estado': item['status'], 'truncada': item['truncated']})
    return keys


def main():
    data = json.loads((MATERIAL / 'cases.json').read_text(encoding='utf-8'))
    validate(data)
    out = ROOT / 'data' / 'pilot' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:6])
    out.mkdir(parents=True, exist_ok=False)
    records = []
    manifest = {'run_id': out.name, 'started_at': timestamp(), 'git_revision': git_revision(),
                'machine': platform.machine(), 'system': platform.platform(), 'options': OPTIONS,
                'split': data['split'], 'planned_responses': 40, 'warmups': [],
                'rubric_review': 'Material v1; double human scoring pending',
                'models': {}, 'material_sha256': {}, 'state': 'running'}
    for filename in ['cases.json', 'RUBRIC.md', 'README.md']:
        content = (MATERIAL / filename).read_bytes()
        manifest['material_sha256'][filename] = hashlib.sha256(content).hexdigest()
        (out / ('snapshot_' + filename)).write_bytes(content)
    manifest['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    shutil.copyfile(__file__, out / 'snapshot_run_pilot.py')
    write_json(out / 'manifest.json', manifest)
    print('RESULTS ' + str(out), flush=True)
    with httpx.Client(base_url='http://127.0.0.1:11434', timeout=180, trust_env=False) as client:
        current = None
        try:
            version = client.get('/api/version')
            version.raise_for_status()
            manifest['ollama'] = version.json()
            for model in MODELS:
                manifest['models'][model] = local_model(client, model)
            # Block order is predeclared in the pilot protocol.
            plan = [(MODELS[0], data['cases'][:10]), (MODELS[1], data['cases'][:10]),
                    (MODELS[1], data['cases'][10:]), (MODELS[0], data['cases'][10:])]
            for block, (model, cases) in enumerate(plan, 1):
                if current and current != model:
                    post(client, '/api/generate', {'model': current, 'keep_alive': 0})
                current = model
                digest = manifest['models'][model]['digest']
                local_model(client, model, digest)
                warm = post(client, '/api/generate', {'model': model, 'prompt': 'Responde solo: listo.',
                            'stream': False, 'keep_alive': '5m', 'options': {**OPTIONS, 'num_predict': 8}})
                if not warm.get('done'):
                    raise RuntimeError('Warmup did not complete')
                manifest['warmups'].append({'block': block, 'model': model,
                    'load_duration_ns': warm.get('load_duration'), 'total_duration_ns': warm.get('total_duration')})
                write_json(out / 'manifest.json', manifest)
                for case in cases:
                    record = {'sequence': len(records) + 1, 'block': block, 'case_id': case['id'],
                              'task': case['task'], 'model': model, 'digest': digest, 'started_at': timestamp()}
                    start = time.perf_counter()
                    try:
                        answer = post(client, '/api/generate', {'model': model, 'prompt': case['prompt'],
                                      'stream': False, 'keep_alive': '5m', 'options': OPTIONS})
                        record.update({key: answer.get(key) for key in ['response', 'done', 'done_reason',
                            'load_duration', 'total_duration', 'prompt_eval_duration', 'eval_duration',
                            'prompt_eval_count', 'eval_count']})
                        if not answer.get('done'):
                            record['status'] = 'error'
                        else:
                            record['status'] = 'completed' if str(answer.get('response', '')).strip() else 'empty'
                    except httpx.TimeoutException:
                        record['status'] = 'timeout'
                    except (httpx.HTTPError, ValueError) as exc:
                        record.update(status='error', error_type=type(exc).__name__)
                    record['wall_seconds'] = round(time.perf_counter() - start, 4)
                    records.append(record)
                    with (out / 'RESTRINGIDO_resultados.jsonl').open('a', encoding='utf-8') as stream:
                        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                    print(f"{len(records):02}/40 {model} {case['id']} {record['status']} {record['wall_seconds']:.2f}s", flush=True)
                    if record['status'] == 'timeout':
                        raise RuntimeError('Stopping after timeout to avoid overlapping inference')
                local_model(client, model, digest)
            manifest['state'] = 'finished'
        except Exception as exc:
            manifest.update(state='interrupted', error_type=type(exc).__name__, error=str(exc))
            raise
        finally:
            if current:
                try:
                    post(client, '/api/generate', {'model': current, 'keep_alive': 0})
                except Exception as exc:
                    manifest['unload_error'] = type(exc).__name__
            manifest.update(finished_at=timestamp(), captured_responses=len(records),
                            statuses=dict(Counter(r['status'] for r in records)))
            write_json(out / 'manifest.json', manifest)
            if records:
                packets(out, data['cases'], records)
            print('FINAL ' + json.dumps({'directory': str(out), 'state': manifest['state'],
                                       'captured': len(records), 'statuses': manifest['statuses']}), flush=True)


if __name__ == '__main__':
    main()
