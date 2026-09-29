"""Validate independent review sheets and report progress without inventing scores."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DIMENSIONS = ['correccion_0_3', 'cobertura_0_3', 'instrucciones_0_3', 'claridad_0_3']
WEIGHTS = [50, 25, 15, 10]
REVIEWERS = ['Maite', 'Arturo']


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def error(context, message):
    raise ValueError(f'{context}: {message}')


def validate_row(row, blind, case, run_id, reviewer):
    context = f"{reviewer}/{blind['response_id']}"
    for field, expected in [('run_id', run_id), ('evaluador', reviewer),
                            ('response_id', blind['response_id']), ('case_id', blind['case_id']),
                            ('estado', blind['status'])]:
        if row.get(field, '').strip() != expected:
            error(context, f'identidad alterada en {field}')
    if row.get('truncada', '').strip().lower() != str(blind['truncated']).lower():
        error(context, 'marca de truncacion alterada')
    scores = []
    for field in DIMENSIONS:
        value = row.get(field, '').strip()
        if value and value not in {'0', '1', '2', '3'}:
            error(context, f'{field} debe ser entero entre 0 y 3 o quedar vacio')
        scores.append(int(value) if value else None)
    critical = row.get('errores_criticos', '').strip()
    critical_ids = None
    if critical:
        if critical.casefold() == 'ninguno':
            critical_ids = []
        else:
            critical_ids = sorted(set(s.strip().upper() for s in critical.split(';')))
            allowed = {f'C{i+1}' for i in range(len(case['critical_errors']))}
            if not set(critical_ids).issubset(allowed):
                error(context, 'usar ninguno o C1;C2 segun el orden de errores del caso')
    code_values = []
    for field in ['pruebas_codigo_superadas', 'pruebas_codigo_total']:
        value = row.get(field, '').strip()
        if value and (not value.isascii() or not value.isdigit()):
            error(context, f'{field} debe ser un entero no negativo o quedar vacio')
        code_values.append(int(value) if value else None)
    evidence = row.get('evidencia', '').strip()
    if blind['status'] != 'completed':
        if any(s is not None for s in scores + code_values) or critical:
            error(context, 'no asignar notas ni pruebas a una generacion fallida')
        return {'state': 'not_evaluable'}
    missing = [name for name, score in zip(DIMENSIONS, scores) if score is None]
    if critical_ids is None:
        missing.append('errores_criticos')
    if case['task'] == 'code':
        passed, total = code_values
        required = len(case['code_tests']['fixtures'])
        if total is not None and total != required:
            error(context, f'el total de pruebas debe ser {required}')
        if passed is not None and (passed > required or total is not None and passed > total):
            error(context, 'pruebas superadas mayor que el total')
        if any(v is None for v in code_values):
            missing.append('pruebas_funcionales_codigo')
    elif any(v is not None for v in code_values):
        error(context, 'pruebas de codigo en una tarea de otra familia')
    if (any(s is not None and s < 3 for s in scores) or critical_ids) and not evidence:
        missing.append('evidencia')
    if missing:
        return {'state': 'pending', 'missing': missing}
    units = sum(w * s for w, s in zip(WEIGHTS, scores))
    return {'state': 'complete', 'scores': scores, 'q_units': units, 'q': units / 300,
            'critical_ids': critical_ids, 'evidence': evidence}


def consolidate(run):
    manifest = read_json(run / 'manifest.json')
    if manifest.get('state') != 'finished' or manifest.get('captured_responses') != 40:
        raise ValueError('Se requiere una ejecucion completa con 40 intentos registrados')
    cases = {c['id']: c for c in read_json(run / 'snapshot_cases.json')['cases']}
    if len(cases) != 20:
        raise ValueError('Conjunto del piloto incompleto')
    evaluations = {}
    originals = None
    hashes = {}
    for reviewer in REVIEWERS:
        folder = run / ('evaluacion_' + reviewer)
        items = read_json(folder / 'respuestas_anonimas.json')
        blind = {item['response_id']: item for item in items}
        if len(blind) != 40 or len(items) != 40:
            raise ValueError(f'{reviewer}: se requieren 40 identificadores unicos')
        if Counter(b['case_id'] for b in items) != Counter({c: 2 for c in cases}):
            raise ValueError(f'{reviewer}: cada caso debe tener dos respuestas')
        if originals is None:
            originals = blind
        elif originals != blind:
            raise ValueError('Los paquetes no contienen las mismas respuestas y metadatos')
        sheet = folder / 'puntuaciones.csv'
        hashes[reviewer] = hashlib.sha256(sheet.read_bytes()).hexdigest()
        with sheet.open(encoding='utf-8-sig', newline='') as stream:
            # Accept comma or semicolon CSV exported by a spreadsheet editor.
            sample = stream.read(8192)
            stream.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=',;')
            reader = csv.DictReader(stream, dialect=dialect)
            required = {'run_id', 'evaluador', 'response_id', 'case_id', 'estado', 'truncada',
                        *DIMENSIONS, 'errores_criticos', 'evidencia',
                        'pruebas_codigo_superadas', 'pruebas_codigo_total'}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f'{reviewer}: faltan columnas obligatorias')
            rows = list(reader)
        if len(rows) != 40 or {r['response_id'] for r in rows} != set(blind):
            raise ValueError(f'{reviewer}: filas ausentes, duplicadas o desconocidas')
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError(f'{reviewer}: alguna fila tiene un numero incorrecto de columnas')
        evaluations[reviewer] = {r['response_id']: validate_row(r, blind[r['response_id']],
            cases[r['case_id']], manifest['run_id'], reviewer) for r in rows}
    progress = {reviewer: dict(Counter(v['state'] for v in entries.values()))
                for reviewer, entries in evaluations.items()}
    ready = all(v['state'] != 'pending' for entries in evaluations.values() for v in entries.values())
    report = {'run_id': manifest['run_id'], 'created_at': datetime.now(timezone.utc).isoformat(),
              'ready': ready, 'progress': progress, 'source_csv_sha256': hashes,
              'pending': {reviewer: {rid: v['missing'] for rid, v in entries.items() if v['state'] == 'pending'}
                          for reviewer, entries in evaluations.items()}}
    if not ready:
        return report
    pairs = []
    for rid in originals:
        a, b = [evaluations[name][rid] for name in REVIEWERS]
        if a['state'] != 'complete' or b['state'] != 'complete':
            continue
        reasons = []
        if a['critical_ids'] != b['critical_ids']:
            reasons.append('errores_criticos')
        if any(abs(x-y) >= 2 for x, y in zip(a['scores'], b['scores'])):
            reasons.append('diferencia_dimension_2_o_mas')
        # Integer units avoid rounding errors at the predeclared 0.15 boundary.
        if abs(a['q_units'] - b['q_units']) > 45:
            reasons.append('diferencia_Q_mayor_0.15')
        pairs.append({'response_id': rid, 'case_id': originals[rid]['case_id'],
                      'task': cases[originals[rid]['case_id']]['task'],
                      'Maite': a, 'Arturo': b, 'review_reasons': reasons,
                      'mean_q_not_consensus': (a['q_units'] + b['q_units']) / 600})
    report['pairs'] = pairs
    report['complete_pairs'] = len(pairs)
    report['review_required'] = sum(bool(p['review_reasons']) for p in pairs)
    report['exact_agreement'] = {name: sum(p['Maite']['scores'][i] == p['Arturo']['scores'][i]
        for p in pairs) / len(pairs) if pairs else None for i, name in enumerate(DIMENSIONS)}
    report['mean_absolute_q_difference'] = sum(abs(p['Maite']['q_units'] - p['Arturo']['q_units'])
        for p in pairs) / (300 * len(pairs)) if pairs else None
    return report


def render(report):
    lines = ['# Estado de la evaluacion del piloto', '', f"Ejecucion: {report['run_id']}", '',
             '| Evaluador | Completas | Pendientes | No evaluables |', '|---|---:|---:|---:|']
    for name, counts in report['progress'].items():
        lines.append(f"| {name} | {counts.get('complete',0)} | {counts.get('pending',0)} | {counts.get('not_evaluable',0)} |")
    if not report['ready']:
        lines.extend(['', 'La evaluacion humana esta pendiente. No se han calculado notas de calidad,',
                      'comparaciones de modelos ni consensos. Las celdas vacias no equivalen a cero.', '',
                      'Completar las cuatro puntuaciones 0-3 y errores_criticos (ninguno o C1;C2).',
                      'Justificar las penalizaciones en evidencia. En codigo, las pruebas funcionales',
                      'deben quedar pendientes hasta ejecutarse en un entorno aislado.'])
    else:
        lines.extend(['', f"Pares evaluables: {report['complete_pairs']}.",
                      f"Respuestas que requieren revision: {report['review_required']}.", '',
                      'El JSON contiene las valoraciones originales y los desacuerdos por respuesta.',
                      'La media de dos notas no constituye un consenso. Resolver y registrar los',
                      'desacuerdos antes de interpretar resultados. No se revela la identidad de modelos.'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    args = parser.parse_args()
    try:
        report = consolidate(args.run_directory)
    except (ValueError, KeyError, OSError, csv.Error) as exc:
        parser.exit(2, f'No se puede consolidar: {exc}\n')
    folder = args.run_directory / 'consolidacion' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'estado.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'ESTADO.md').write_text(render(report), encoding='utf-8')
    print(render(report))
    print(f'Informe conservado en: {folder}')


if __name__ == '__main__':
    main()
