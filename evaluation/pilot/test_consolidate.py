import csv
import json
import tempfile
import unittest
from pathlib import Path

from consolidate import DIMENSIONS, consolidate
from run_pilot import MATERIAL, packets


class ConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run = Path(self.temp.name)
        self.data = json.loads((MATERIAL / 'cases.json').read_text())
        self.cases = {c['id']: c for c in self.data['cases']}
        records = [{'case_id': c['id'], 'model': model, 'digest': 'digest', 'sequence': i,
                    'status': 'completed', 'done_reason': 'stop', 'response': 'Texto ficticio.'}
                   for model in ['a', 'b'] for i, c in enumerate(self.data['cases'])]
        packets(self.run, self.data['cases'], records)
        (self.run / 'snapshot_cases.json').write_text(json.dumps(self.data))
        (self.run / 'manifest.json').write_text(json.dumps({'run_id': self.run.name,
            'state': 'finished', 'captured_responses': 40}))

    def tearDown(self):
        self.temp.cleanup()

    def edit(self, reviewer, change):
        path = self.run / ('evaluacion_' + reviewer) / 'puntuaciones.csv'
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        change(rows)
        with path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def fill(self, value='3'):
        def apply(rows):
            for row in rows:
                row.update({field: value for field in DIMENSIONS})
                row.update(errores_criticos='ninguno', evidencia='Evidencia ficticia de prueba.')
                case = self.cases[row['case_id']]
                if case['task'] == 'code':
                    count = len(case['code_tests']['fixtures'])
                    row['pruebas_codigo_total'] = str(count)
                    row['pruebas_codigo_superadas'] = str(count if value == '3' else 0)
        for reviewer in ['Maite', 'Arturo']:
            self.edit(reviewer, apply)

    def test_blank_is_pending_not_zero(self):
        report = consolidate(self.run)
        self.assertFalse(report['ready'])
        self.assertNotIn('pairs', report)
        self.assertEqual(report['progress']['Maite'], {'pending': 40})

    def test_complete_scores_and_agreement(self):
        self.fill()
        report = consolidate(self.run)
        self.assertTrue(report['ready'])
        self.assertEqual(report['complete_pairs'], 40)
        self.assertEqual(report['review_required'], 0)
        self.assertTrue(all(p['mean_q_not_consensus'] == 1 for p in report['pairs']))
        self.assertTrue(all(v == 1 for v in report['exact_agreement'].values()))

    def test_zero_is_a_valid_recorded_score(self):
        self.fill('0')
        report = consolidate(self.run)
        self.assertTrue(report['ready'])
        self.assertTrue(all(p['Maite']['q'] == 0 for p in report['pairs']))

    def test_invalid_value_and_duplicate_are_rejected(self):
        self.edit('Maite', lambda rows: rows[0].update(correccion_0_3='4'))
        with self.assertRaises(ValueError):
            consolidate(self.run)
        self.edit('Maite', lambda rows: rows.__setitem__(1, dict(rows[0])))
        with self.assertRaisesRegex(ValueError, 'duplicadas'):
            consolidate(self.run)

    def test_missing_code_checks_remain_pending(self):
        self.fill()
        self.edit('Arturo', lambda rows: next(r for r in rows if r['case_id'] == 'C01').update(pruebas_codigo_total=''))
        report = consolidate(self.run)
        self.assertFalse(report['ready'])
        self.assertEqual(report['progress']['Arturo']['pending'], 1)
        self.assertNotIn('pairs', report)

    def test_penalty_requires_evidence(self):
        self.fill()
        self.edit('Maite', lambda rows: rows[0].update(claridad_0_3='2', evidencia=''))
        report = consolidate(self.run)
        self.assertFalse(report['ready'])
        self.assertEqual(report['progress']['Maite']['pending'], 1)

    def test_disagreement_boundary_and_critical_ids(self):
        self.fill()
        self.edit('Arturo', lambda rows: next(r for r in rows if r['case_id'] == 'K01').update(
            instrucciones_0_3='0', errores_criticos='C1'))
        report = consolidate(self.run)
        pair = next(p for p in report['pairs'] if p['review_reasons'])
        self.assertIn('errores_criticos', pair['review_reasons'])
        self.assertIn('diferencia_dimension_2_o_mas', pair['review_reasons'])
        self.assertNotIn('diferencia_Q_mayor_0.15', pair['review_reasons'])


if __name__ == '__main__':
    unittest.main()
