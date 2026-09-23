"""Application tests with synthetic inputs; never live demonstration evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from inspecta_scp.api import Application
from inspecta_scp.approvals import Approvals
from inspecta_scp.config import PolicyError, resolve
from inspecta_scp.controller import Controller
from inspecta_scp.knowledge import Knowledge
from inspecta_scp.sources import Sources


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.books = self.root / 'books'
        self.books.mkdir()
        self.path = self.books / 'final_verified.json'
        self.path.write_text(json.dumps([{'rule_id': 'MR-TEST', 'principle': 'retain state', 'confidence': .8}]))
        self.c = Controller(self.root / 'state')
        self.k = Knowledge(self.c.store)
        self.s = Sources(self.c.store)
        self.a = Approvals(self.c.store)

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def source(self, role='learning'):
        root = self.s.register_root(self.books, role)
        return self.s.register(root['id'], self.path.name)

    def candidate(self):
        value = json.loads((Path(__file__).parent / 'fixtures/synthetic-rule.json').read_text())
        source = self.source()
        value.update(source_references=[source['id']], source_artifact_hashes=[source['sha256']],
                     target_compatibility=['synthetic-test-profile'])
        return value

    def test_retrieval_threshold_bounds_and_filtering(self):
        self.k.propose(self.candidate())
        self.assertEqual(self.k.retrieve('zzzznooverlap', 'repair-system', 'synthetic-test-profile'), [])
        rule=self.candidate()
        exact=rule['trigger']+' '+rule['principle']
        self.assertEqual(len(self.k.retrieve(exact, 'repair-system', 'synthetic-test-profile', distance_threshold=0.1)),1)
        for value in [-0.1,0.31,float('nan'),True,'0.1']:
            with self.assertRaises(PolicyError):
                self.k.retrieve('state', 'repair-system', 'synthetic-test-profile', distance_threshold=value)

    def test_import_preserves_original_and_deduplicates(self):
        before = self.path.read_bytes()
        first = self.k.import_books(self.books)
        self.assertEqual(first, self.k.import_books(self.books))
        self.assertEqual(self.path.read_bytes(), before)
        rule = self.k.catalog()['rules'][0]
        self.assertEqual(rule['status'], 'SOURCE_ONLY_PENDING_REVIEW')
        self.assertEqual(rule['variants'][0]['original_forecast']['score'], .8)
        self.assertEqual(len(self.c.store.records('release')), 0)

    def test_conflicting_variants_preserved(self):
        (self.books / 'second.json').write_text(json.dumps([{'rule_id': 'MR-TEST', 'principle': 'discard state'}]))
        self.k.import_books(self.books)
        rule = self.k.catalog()['rules'][0]
        self.assertEqual(len(rule['variants']), 2)
        self.assertEqual(rule['status'], 'CONFLICT_REVIEW_REQUIRED')

    def test_evaluator_and_hidden_import_excluded(self):
        for name in ['golden_examples', '.private']:
            folder = self.books / name
            folder.mkdir()
            (folder / 'answer.txt').write_text('MR-SECRET')
        self.assertEqual(self.k.import_books(self.books)['document_count'], 1)

    def test_human_snapshot_survives_stale_original(self):
        source = self.source('shared')
        before = self.s.view(source['id'])['text']
        self.path.write_text('changed')
        view = self.s.view(source['id'])
        self.assertEqual(view['text'], before)
        self.assertEqual(view['freshness'], 'STALE')
        with self.assertRaises(PolicyError):
            self.s.view(source['id'], 'generator')

    def test_learning_and_evaluator_never_generator_visible(self):
        for role in ['learning', 'evaluator']:
            source = self.source(role)
            with self.assertRaises(PolicyError):
                self.s.view(source['id'], 'generator')

    def test_replaced_root_symlink_blocked(self):
        source = self.source('shared')
        moved = self.root / 'moved'
        self.books.rename(moved)
        self.books.symlink_to(moved, target_is_directory=True)
        self.assertEqual(self.s.view(source['id'])['freshness'], 'BROKEN')
        with self.assertRaises(PolicyError):
            self.s.register(source['root_id'], self.path.name)

    def test_exact_source_passage_and_tamper(self):
        self.path.write_text('one\n<script>window.bad=1</script>\nthree\n')
        source = self.source()
        self.assertEqual(self.s.view(source['id'], start=2, end=2)['text'], '<script>window.bad=1</script>\n')
        (self.c.store.root / source['content']['path']).write_text('{}')
        with self.assertRaises(PolicyError):
            self.s.view(source['id'])

    def test_candidate_provenance_and_no_self_approval(self):
        candidate = self.candidate()
        self.k.propose(candidate)
        for extra in [{'state': 'TESTED'}, {'formal_pattern_status': 'TOOL_VALIDATED'}, {'source_artifact_hashes': ['wrong']}]:
            with self.subTest(extra=extra), self.assertRaises(PolicyError):
                self.k.propose({**candidate, **extra})

    def test_candidate_evaluator_provenance_rejected(self):
        candidate = self.candidate()
        source = self.source('evaluator')
        candidate.update(source_references=[source['id']], source_artifact_hashes=[source['sha256']])
        with self.assertRaises(PolicyError):
            self.k.propose(candidate)

    def test_release_excludes_source_archives_and_requires_checks(self):
        candidate = self.candidate()
        candidate['counterexample']['source_or_test_reference'] = 'private/answer.json'
        key = self.k.propose(candidate)['id']
        draft = self.k.draft_release([key])
        exported = draft['rules'][0]['record']
        self.assertNotIn('source_references', exported)
        self.assertNotIn('source_or_test_reference', exported['counterexample'])
        request = self.k.request_publication(draft['id'])
        self.a.decide(request['id'], request['subject_digest'], 'APPROVED', 'synthetic-test-reviewer')
        with self.assertRaisesRegex(PolicyError, 'validation/transfer'):
            self.k.publish(draft['id'], request['id'])

    def test_retrieval_filters_before_ranking(self):
        self.k.propose(self.candidate())
        self.assertEqual(self.k.retrieve('state', 'repair-system', 'wrong-profile'), [])
        rule=self.candidate()
        self.assertEqual(len(self.k.retrieve(rule['trigger']+' '+rule['principle'], 'repair-system', 'synthetic-test-profile')), 1)

    def test_forecast_preserves_question_without_empirical_claim(self):
        forecast = json.loads((Path(__file__).parent / 'fixtures/synthetic-confidence.json').read_text())
        saved = self.k.forecast(forecast)
        self.assertEqual(saved['record'], forecast)
        self.assertEqual(saved['provenance_status'], 'IMPORTED_FORECAST_PENDING_MODEL_EVENT_CORROBORATION')
        with self.assertRaises(PolicyError):
            self.k.forecast({**forecast, 'status': 'REPORTED', 'exact_question': ''})

    def test_role_binding_rejects_swaps_and_remains_unvalidated(self):
        candidate = self.candidate()
        candidate['parameters'] = [{'name': 'sensor', 'role': 'input', 'constraints': 'reviewed owner'},
                                   {'name': 'actuator', 'role': 'output', 'constraints': 'reviewed owner'}]
        key = self.k.propose(candidate)['id']
        roles = {'a': {'role': 'input', 'evidence_reference': 'test-only'},
                 'b': {'role': 'output', 'evidence_reference': 'test-only'}}
        binding = self.k.bind(key, 'repair-system', 'synthetic-test-profile', roles,
                              {'sensor': 'a', 'actuator': 'b'}, ['TEST-REQ'])
        self.assertEqual(binding['status'], 'DRAFT_REQUIRES_LEDGER_AND_ARCHITECTURE_CHECK')
        with self.assertRaises(PolicyError):
            self.k.bind(key, 'repair-system', 'synthetic-test-profile', roles,
                        {'sensor': 'b', 'actuator': 'a'}, ['TEST-REQ'])

    def test_approval_exact_subject_replay_and_revocation(self):
        request = self.a.request('increase_budget', {'tokens': 100})
        with self.assertRaises(PolicyError):
            self.a.decide(request['id'], 'wrong', 'APPROVED', 'tester')
        self.a.decide(request['id'], request['subject_digest'], 'APPROVED', 'tester')
        with self.assertRaises(PolicyError):
            self.a.require(request['id'], 'increase_budget', {'tokens': 101})
        with self.assertRaises(PolicyError):
            self.a.decide(request['id'], request['subject_digest'], 'APPROVED', 'tester')
        self.a.decide(request['id'], request['subject_digest'], 'REVOKED', 'tester')
        with self.assertRaises(PolicyError):
            self.a.require(request['id'], 'increase_budget', {'tokens': 100})

    def profile(self):
        (self.books / 'Model.sysml').write_text('package Test {}')
        return {'project': str(self.books), 'input_files': ['Model.sysml'], 'model_file': 'Model.sysml',
                'task_operation': 'verify-only', 'budget': {'aggregate_model_tokens': 100, 'wall_seconds': 60}}

    def test_budget_amendment_keeps_usage_and_elapsed_time(self):
        run = self.c.create(self.profile())
        self.c.store.db.execute('UPDATE runs SET used_tokens=17,usage_unknown=1 WHERE id=?', (run['id'],))
        request = self.c.request_budget(run['id'], 200, 120)
        with self.assertRaises(PolicyError):
            self.c.amend_budget(run['id'], request['id'])
        self.a.decide(request['id'], request['subject_digest'], 'APPROVED', 'tester')
        updated = self.c.amend_budget(run['id'], request['id'])
        self.assertEqual(updated['deadline'], run['created'] + 120)
        self.assertEqual(updated['used_tokens'], 17)
        self.assertIsNone(updated['remaining_tokens'])
        self.assertEqual(updated['state'], 'PAUSED')
        with self.assertRaises(PolicyError):
            self.c.amend_budget(run['id'], request['id'])

    def test_api_and_controller_parity_and_scope(self):
        profile = self.root / 'test.json'
        data = self.profile()
        profile.write_text(json.dumps(data))
        app = Application(self.c.store.root, [profile], [self.books])
        request = {'profile_id': 'test', 'overrides': {'budget': {'wall_seconds': 90}}}
        self.assertEqual(app.call('POST', '/api/resolve', request), resolve(data, request['overrides'], profile.parent))
        run = app.call('POST', '/api/runs', request)
        self.assertEqual(app.call('POST', '/api/runs/' + run['id'] + '/pause')['state'], 'PAUSED')
        resumed = app.call('POST', '/api/runs/' + run['id'] + '/resume')
        self.assertEqual(resumed['deadline'], run['deadline'])
        with self.assertRaises(PolicyError):
            app.call('POST', '/api/runs', {'profile_id': 'test', 'overrides': {'project': '/tmp'}})
        with self.assertRaises(PolicyError):
            app.call('POST', '/api/library/import', {'root_id': '/tmp'})


if __name__ == '__main__':
    unittest.main()
