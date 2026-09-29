"""Validate pilot material and render a readable casebook, without inference."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FAMILIES = {'knowledge': 'K', 'reasoning': 'R', 'code': 'C', 'summary': 'S', 'writing': 'W'}


def validate(data):
    assert data['version'] == 'pilot-v1'
    assert data['split'] == 'pilot_only'
    cases = data['cases']
    assert len(cases) == 20
    assert Counter(c['task'] for c in cases) == {k: 4 for k in FAMILIES}
    assert len({c['prompt'] for c in cases}) == 20
    assert {c['id'] for c in cases} == {f'{p}{n:02}' for p in FAMILIES.values() for n in range(1, 5)}
    for c in cases:
        assert c['id'].startswith(FAMILIES[c['task']])
        assert c['privacy'] in {'public', 'internal', 'sensitive'}
        assert isinstance(c['allow_remote'], bool)
        assert len(c['expected_points']) == 3
        for key in ('expected_points', 'critical_errors', 'format_checks'):
            assert c[key] and all(isinstance(s, str) and s.strip() for s in c[key])
        assert c['prompt'].strip() and len(c['prompt']) < 20000
        if c['task'] == 'code':
            spec = c['code_tests']
            assert spec['preserve_inputs'] is True
            assert spec['function'] in c['prompt']
            assert len(spec['fixtures']) >= 4
            for fixture in spec['fixtures']:
                assert isinstance(fixture['args'], list) and len(fixture['args']) == 1
                assert 'expected' in fixture
    assert sum(c['privacy'] == 'sensitive' for c in cases) >= 3
    assert any(c['privacy'] == 'internal' and c['allow_remote'] for c in cases)


def render(data):
    lines = ['# Cuaderno de casos del piloto v1', '',
             'Generado desde `cases.json`. Contiene criterios reservados a los evaluadores.',
             'Al modelo se envia exclusivamente el texto del enunciado.', '']
    for c in data['cases']:
        lines.extend([f"## {c['id']}: {c['title']}", '',
                      f"Familia: {c['task']} | Dificultad propuesta: {c['difficulty']} | Privacidad: {c['privacy']} | Autorizacion remota: {c['allow_remote']}", '',
                      '### Enunciado', '', c['prompt'], '', '### Puntos esperados', ''])
        lines.extend(f'- {point}' for point in c['expected_points'])
        lines.extend(['', '### Errores criticos', ''])
        lines.extend(f'- {error}' for error in c['critical_errors'])
        lines.extend(['', '### Formato', ''])
        lines.extend(f'- {check}' for check in c['format_checks'])
        if 'code_tests' in c:
            lines.extend(['', '### Pruebas de referencia', '', '```json',
                          json.dumps(c['code_tests'], indent=2, ensure_ascii=False), '```'])
        if 'expected_json' in c:
            lines.extend(['', '### Objeto esperado', '', '```json',
                          json.dumps(c['expected_json'], indent=2, ensure_ascii=False), '```'])
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


if __name__ == '__main__':
    data = json.loads((ROOT / 'cases.json').read_text(encoding='utf-8'))
    validate(data)
    (ROOT / 'CASES.md').write_text(render(data), encoding='utf-8')
    print('20 casos validados: 4 por familia. Cuaderno generado en evaluation/pilot/CASES.md')
