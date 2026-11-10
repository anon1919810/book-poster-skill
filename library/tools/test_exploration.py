import copy
import shutil
import json
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path

import library
from retrieval import search, normalize_query, browser_engine
from test_retrieval import case


class ExplorationTests(unittest.TestCase):
    def setUp(self):
        self.items = [case(f'P-{i:04d}', creator=str(i)) for i in range(1, 13)]
        for item in self.items:
            item['source_url'] = 'https://example.org/work/' + item['id']

    def query(self, items=None, query='', **kw):
        return search(self.items if items is None else items, query, library.ALIASES, library.CONTROLLED, **kw)

    def test_short_aliases_and_unknown_word_boundaries(self):
        self.assertEqual(normalize_query('瑞士 留白 网格 超现实 重复 旋转', library.ALIASES),
                         ['swiss_international', 'negative_space', 'grid', 'surrealism', '重复', '旋转'])
        self.assertEqual(normalize_query('摄影师 身份证 空间站', library.ALIASES), ['摄影师', '身份证', '空间站'])
        self.assertEqual(normalize_query('瑞士国际主义几何秩序', library.ALIASES), ['swiss_international', 'geometric_order'])

    def test_seed_is_reproducible_permutation_independent_and_explores(self):
        for seed in ['book-a', '书籍乙']:
            self.assertEqual(self.query(seed=seed), self.query(list(reversed(self.items)), seed=seed))
        winners = {self.query(seed=str(i), limit=1)[0]['id'] for i in range(50)}
        self.assertGreaterEqual(len(winners), 8)
        self.assertNotEqual([r['id'] for r in self.query(seed='book-a')], sorted(r['id'] for r in self.query(seed='book-a')))

    def test_recency_is_soft_and_cannot_overturn_relevance(self):
        first = self.query(seed='same', limit=1)[0]['id']
        counts = {first: {'shown': 3, 'used': 2}}
        changed = self.query(seed='same', usage_counts=counts)
        self.assertNotEqual(changed[0]['id'], first)
        all_rows = self.query(seed='same', usage_counts=counts, limit=None)
        self.assertIn(first, [r['id'] for r in all_rows])
        hit = next(r for r in all_rows if r['id'] == first)
        self.assertGreater(hit['context_penalty'], 0)
        unique = copy.deepcopy(self.items)
        unique[0]['art_history'] = [{'term_id': 'swiss_international', 'relation': 'visual_affinity'}]
        rows = self.query(unique, query='geometric_order swiss_international', diverse=True,
                          usage_counts={unique[0]['id']: {'shown': 99, 'used': 99}})
        self.assertEqual(rows[0]['id'], unique[0]['id'])

    def test_shared_collection_page_does_not_pin_earliest_work(self):
        items = copy.deepcopy(self.items[:3])
        for item in items: item['source_url'] = 'https://museum.example/group'
        winners = {self.query(items, seed=str(i), limit=1)[0]['id'] for i in range(50)}
        self.assertEqual(len(winners), 3)
        self.assertEqual(len({r['tie_break'] for r in self.query(items, seed='same')}), 3)

    def test_batch_ids_and_context_browser_parity(self):
        options = {'seed': '三本书', 'diverse': True, 'limit': 7,
                   'usage_counts': {'P-0001': {'shown': 2, 'used': 1}}, 'batch_ids': ['P-0002']}
        for item in self.items[:3]: item['source_url']='https://museum.example/group'
        rows = self.query(query='几何 秩序', **options)
        self.assertTrue(any(r['batch_repeat'] for r in self.query(batch_ids=['P-0002'], limit=None)))
        node = shutil.which('node')
        if not node: self.skipTest('Node unavailable')
        code = browser_engine(library.ALIASES, library.CONTROLLED)
        code += '\nprocess.stdout.write(JSON.stringify(PosterSearch.search(' + json.dumps(self.items) + ',' + json.dumps('几何 秩序') + ',' + json.dumps(options) + ')));'
        actual = json.loads(subprocess.check_output([str(node), '-e', code], text=True, encoding='utf-8'))
        self.assertEqual(rows, actual)


class UsageTests(unittest.TestCase):
    def test_history_lifecycle_and_read_only_search(self):
        from usage import record_event, load_events, usage_counts, UsageError
        ids = {'P-0001', 'P-0002'}
        event = {'event_id': 'e1', 'task_id': 't1', 'timestamp': '2026-11-08T12:00:00+08:00',
                 'shown_ids': ['P-0001', 'P-0002'], 'used_ids': ['P-0001'], 'route_skeletons': []}
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'usage.jsonl'
            self.assertEqual(load_events(ledger, ids), [])
            self.assertFalse(ledger.exists())
            self.assertTrue(record_event(ledger, event, ids))
            before = ledger.read_bytes()
            self.assertFalse(record_event(ledger, event, ids))
            self.assertEqual(before, ledger.read_bytes())
            events = load_events(ledger, ids)
            self.assertEqual(usage_counts(events, 20)['P-0001'], {'shown': 1, 'used': 1})
            search([case('P-0001'), case('P-0002')], '', library.ALIASES, library.CONTROLLED,
                   usage_counts=usage_counts(events, 20))
            self.assertEqual(before, ledger.read_bytes())
            other = dict(event, event_id='e2', used_ids=['P-0002'])
            record_event(ledger, other, ids)
            counts = usage_counts(load_events(ledger, ids), 20)
            self.assertEqual(counts['P-0001']['shown'], 1)
            self.assertEqual(counts['P-0002']['used'], 1)
            record_event(ledger, dict(event, event_id='e3', task_id='t2', shown_ids=['P-0002'], used_ids=[]), ids)
            self.assertEqual(usage_counts(load_events(ledger, ids), 1), {'P-0002': {'shown': 1, 'used': 0}})
            with self.assertRaises(UsageError): record_event(ledger, dict(event, used_ids=[]), ids)
            with self.assertRaises(UsageError): record_event(ledger, dict(event, event_id='bad', used_ids=['P-9999']), ids)
            ledger.write_text('{broken', encoding='utf-8')
            with self.assertRaises(UsageError): load_events(ledger, ids)

    def test_invalid_event_shapes_and_recent_window(self):
        from usage import validate_event, usage_counts, UsageError
        good = {'event_id': 'e1', 'task_id': 't1', 'timestamp': '2026-11-08T01:00:00Z',
                'shown_ids': ['P-0001'], 'used_ids': []}
        for update in ({'timestamp': 'yesterday'}, {'timestamp': '2026-11-08'},
                       {'shown_ids': 'P-0001'}, {'shown_ids': ['P-0001', 'P-0001']},
                       {'route_skeletons': [{}]}, {'event_id': ''}, {'user_likes': True}):
            with self.subTest(update=update), self.assertRaises(UsageError):
                validate_event(dict(good, **update), {'P-0001'})
        self.assertEqual(usage_counts([good], 0), {})
        with self.assertRaises(UsageError): usage_counts([good], -1)

    def test_usage_cli_roundtrip_and_errors(self):
        # An empty library is valid and sufficient to test an empty, explicit event.
        cli = Path(__file__).with_name('library.py')
        event = {'event_id': 'e1', 'task_id': 't1', 'timestamp': '2026-11-08T01:00:00Z',
                 'shown_ids': [], 'used_ids': []}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); file=root/'event.json'; ledger=root/'usage.jsonl'
            file.write_text(json.dumps(event), encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable, '-X', 'utf8', str(cli), *args, '--root', str(root)],
                                      capture_output=True, text=True, encoding='utf-8')
            args=['record-usage', '--usage-ledger', str(ledger), '--event', str(file)]
            self.assertEqual(run(*args).returncode, 0)
            before=ledger.read_bytes()
            self.assertIn('already recorded',run(*args).stdout)
            self.assertEqual(run('search','--usage-ledger',str(ledger)).returncode, 0)
            self.assertEqual(ledger.read_bytes(), before)
            ledger.write_text('{broken',encoding='utf-8')
            failed=run('search','--usage-ledger',str(ledger))
            self.assertNotEqual(failed.returncode,0)
            self.assertIn('Invalid ledger',failed.stderr)
            self.assertNotIn('Traceback',failed.stderr)


if __name__ == '__main__': unittest.main()
