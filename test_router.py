import json
from pathlib import Path
import tempfile
import unittest
import httpx
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from pydantic import ValidationError
import app
from router import RouteRequest, route, WEIGHTS


class RoutingTests(unittest.TestCase):
    def request(self, **kwargs):
        return RouteRequest(prompt='Texto de prueba para resumir', **kwargs)

    def test_privacy_is_hard_constraint_for_every_profile(self):
        for privacy in ['internal', 'sensitive']:
            for profile in WEIGHTS:
                result = route(self.request(privacy=privacy, allow_remote=True, profile=profile))
                self.assertEqual(result['selected']['location'], 'local')
                self.assertFalse(result['candidates'][2]['eligible'])

    def test_remote_requires_opt_in(self):
        self.assertEqual(route(self.request(privacy='public', profile='quality'))['selected']['location'], 'local')

    def test_remote_selected_when_only_one_meets_quality(self):
        result = route(self.request(privacy='public', allow_remote=True, profile='quality', min_quality=.93))
        self.assertEqual(result['selected']['id'], 'remote')

    def test_cost_prefers_compact(self):
        self.assertEqual(route(self.request(profile='cost'))['selected']['id'], 'local-small')

    def test_sensitive_heuristic_overrides_public_label(self):
        req = RouteRequest(prompt='Email de contacto: ana@example.org', privacy='public', allow_remote=True)
        result = route(req)
        self.assertTrue(result['analysis']['sensitive_signal'])
        self.assertFalse(result['candidates'][2]['eligible'])

    def test_zero_budget_abstains(self):
        result = route(self.request(max_cost=0))
        self.assertIsNone(result['selected'])
        self.assertEqual(result['status'], 'abstained')

    def test_quality_constraint_abstains(self):
        self.assertIsNone(route(self.request(min_quality=1))['selected'])

    def test_bounds_do_not_change_with_privacy_filter(self):
        a = route(self.request(privacy='public', allow_remote=True))
        b = route(self.request(privacy='sensitive'))
        self.assertEqual(a['bounds'], b['bounds'])
        self.assertEqual(a['candidates'][0]['score'], b['candidates'][0]['score'])

    def test_scores_and_weights(self):
        for profile, weights in WEIGHTS.items():
            self.assertAlmostEqual(sum(weights), 1)
            result = route(self.request(profile=profile))
            for candidate in result['candidates']:
                if candidate['eligible']:
                    self.assertAlmostEqual(candidate['score'], sum(candidate['contributions']))
                    self.assertTrue(0 <= candidate['score'] <= 1)

    def test_invalid_input(self):
        for args in [{'prompt':' '}, {'prompt':'x', 'max_cost':-1}, {'prompt':'x', 'max_cost':float('nan')},
                     {'prompt':'x', 'profile':'anything'}, {'prompt':'x', 'output_tokens':999999}]:
            with self.assertRaises(ValidationError):
                RouteRequest(**args)

    def test_no_prompt_in_result(self):
        result = route(self.request())
        self.assertNotIn('Texto de prueba', json.dumps(result))
        self.assertEqual(result['metric_source'], 'synthetic-demonstration')


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(app, 'DB_PATH', Path(self.tmp.name)/'test.sqlite')
        self.db_patch.start()
        self.client = TestClient(app.app)
        self.headers = {'x-session-token': self.client.get('/api/config').json()['token']}

    def tearDown(self):
        self.client.close()
        self.db_patch.stop()
        self.tmp.cleanup()

    def test_session_protection(self):
        self.assertEqual(self.client.post('/api/route', json={'prompt':'x'}).status_code, 403)

    def test_host_protection(self):
        self.assertEqual(self.client.get('/api/config', headers={'host':'attacker.example'}).status_code,403)

    def test_history_and_deletion(self):
        res = self.client.post('/api/route', json={'prompt':'Secret prompt'}, headers=self.headers)
        self.assertEqual(res.status_code,200)
        data = self.client.get('/api/history').json()
        self.assertEqual(len(data),1)
        self.assertNotIn('Secret prompt',json.dumps(data))
        self.assertEqual(self.client.delete('/api/history',headers=self.headers).status_code,200)
        self.assertEqual(self.client.get('/api/history').json(),[])

    def test_unconfigured_execution_never_contacts_provider(self):
        with patch.object(app.httpx, 'Client') as client:
            res = self.client.post('/api/execute', json={'prompt':'x'}, headers=self.headers)
            self.assertEqual(res.status_code,409)
            client.assert_not_called()
        record = self.client.get('/api/history').json()[0]
        self.assertEqual(record['execution']['status'], 'blocked')
        self.assertEqual(record['execution']['reason'], 'destination_not_configured')

    def test_provider_failure_is_recorded_without_content(self):
        with patch.dict(app.LOCAL_BINDINGS, {'local-small':'test-local'}), patch.object(app.httpx,'Client') as client:
            client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError('unavailable')
            res = self.client.post('/api/execute', json={'prompt':'Private request', 'profile':'cost'}, headers=self.headers)
            self.assertEqual(res.status_code,502)
        records = self.client.get('/api/history').json()
        self.assertEqual(records[0]['execution']['status'], 'failed')
        self.assertNotIn('Private request',json.dumps(records))

    def test_database_rolls_back_and_closes_on_error(self):
        with self.assertRaises(RuntimeError):
            with app.database() as conn:
                conn.execute('INSERT INTO decisions VALUES (?, ?)', ('rollback','{}'))
                raise RuntimeError('test rollback')
        self.assertEqual(self.client.get('/api/history').json(),[])
        with self.assertRaises(Exception):
            conn.execute('SELECT 1')

    def test_remote_execution_is_disabled(self):
        with patch.object(app.httpx, 'Client') as client:
            res = self.client.post('/api/execute', json={'prompt':'x', 'privacy':'public', 'allow_remote':True, 'profile':'quality', 'min_quality':.93}, headers=self.headers)
            self.assertEqual(res.status_code,409)
            client.assert_not_called()

    def test_local_execution_with_mock_provider(self):
        fake = MagicMock()
        fake.get.return_value.json.return_value = {'models':[{'name':'test-local', 'digest':'test-digest'}]}
        info = MagicMock(); info.json.return_value = {'details':{'family':'test'}}
        completion = MagicMock(); completion.json.return_value = {'response':'Respuesta local', 'done':True, 'eval_count':3}
        fake.post.side_effect = [info, completion]
        with patch.dict(app.LOCAL_BINDINGS, {'local-small':'test-local'}), patch.object(app.httpx,'Client') as client:
            client.return_value.__enter__.return_value=fake
            res=self.client.post('/api/execute',json={'prompt':'x','profile':'cost'},headers=self.headers)
            self.assertEqual(res.status_code,200)
            self.assertEqual(res.json()['response'],'Respuesta local')
            history=self.client.get('/api/history').json()
            self.assertNotIn('Respuesta local',json.dumps(history))
            self.assertFalse(history[0]['execution']['energy_measured'])
            self.assertEqual(history[0]['execution']['model_digest'], 'test-digest')
            self.assertEqual(history[0]['execution']['context_tokens'], 4096)
            payload = fake.post.call_args.kwargs['json']
            self.assertEqual(payload['options']['num_ctx'], 4096)
            self.assertEqual(payload['keep_alive'], '2m')

    def test_cloud_alias_is_blocked(self):
        fake=MagicMock()
        fake.get.return_value.json.return_value={'models':[{'name':'innocent-alias','remote_host':'https://cloud.example'}]}
        with patch.dict(app.LOCAL_BINDINGS, {'local-small':'innocent-alias'}), patch.object(app.httpx,'Client') as client:
            client.return_value.__enter__.return_value=fake
            res=self.client.post('/api/execute',json={'prompt':'x','profile':'cost'},headers=self.headers)
            self.assertEqual(res.status_code,409)
            fake.post.assert_not_called()
        record = self.client.get('/api/history').json()[0]
        self.assertEqual(record['execution']['status'], 'blocked')
        self.assertEqual(record['execution']['reason'], 'local_model_required')


if __name__ == '__main__':
    unittest.main()
