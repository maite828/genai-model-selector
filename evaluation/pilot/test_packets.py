import csv
import json
import tempfile
import unittest
from pathlib import Path

from run_pilot import MATERIAL, packets


class PacketTests(unittest.TestCase):
    def test_reviewers_receive_same_complete_set_without_model_metadata(self):
        cases = json.loads((MATERIAL / 'cases.json').read_text())['cases']
        records = []
        for model in ['private-model-a', 'private-model-b']:
            for case in cases:
                records.append({'case_id': case['id'], 'model': model, 'digest': 'private-digest',
                                'sequence': len(records) + 1, 'status': 'completed',
                                'done_reason': 'stop', 'response': 'Respuesta de prueba.'})
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            keys = packets(out, cases, records)
            ids = {k['response_id'] for k in keys}
            self.assertEqual(len(ids), 40)
            for reviewer in ['Maite', 'Arturo']:
                folder = out / ('evaluacion_' + reviewer)
                blind = json.loads((folder / 'respuestas_anonimas.json').read_text())
                self.assertEqual({b['response_id'] for b in blind}, ids)
                for path in folder.iterdir():
                    text = path.read_text(encoding='utf-8-sig')
                    self.assertNotIn('private-model', text)
                    self.assertNotIn('private-digest', text)
                with (folder / 'puntuaciones.csv').open(encoding='utf-8-sig', newline='') as stream:
                    rows = list(csv.DictReader(stream))
                self.assertEqual(len(rows), 40)
                self.assertTrue(all(r['correccion_0_3'] == '' and r['evidencia'] == '' for r in rows))

    def test_response_is_preserved_and_not_interpreted_as_document_markup(self):
        cases = json.loads((MATERIAL / 'cases.json').read_text())['cases']
        response = '# Heading\n<script>example</script>\n```python\nprint(1)\n```'
        record = {'case_id': 'K01', 'model': 'private', 'digest': 'digest', 'sequence': 1,
                  'status': 'completed', 'done_reason': 'length', 'response': response}
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            packets(out, cases, [record])
            folder = out / 'evaluacion_Maite'
            entry = json.loads((folder / 'respuestas_anonimas.json').read_text())[0]
            self.assertEqual(entry['response'], response)
            self.assertTrue(entry['truncated'])
            self.assertIn('    <script>example</script>', (folder / 'CUADERNO.md').read_text())


if __name__ == '__main__':
    unittest.main()
