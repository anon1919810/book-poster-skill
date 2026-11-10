"""Exercise real file staging with isolated fixtures."""
import base64
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from staging import StageError, stage


PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+'
    'A8AAQUBAScY42YAAAAASUVORK5CYII='
)
CLI = Path(__file__).with_name('library.py')


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='poster-stage-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / '原始资料库 with spaces'
        self.dest = self.base / '本次任务' / '参考图'
        self.records = {}
        for cid in ('P-0001', 'P-0002'):
            folder = self.root / 'cases' / cid
            folder.mkdir(parents=True)
            (folder / 'preview.png').write_bytes(PNG)
            record = {
                'id': cid, 'title': '真实海报', 'creator': 'Designer', 'year': '1955',
                'image_path': f'cases/{cid}/preview.png',
                'source_url': 'https://example.org/record',
                'image_url': 'https://example.org/image',
                'rights_note': 'Research only', 'annotation_status': 'draft',
                'art_history': [{'term_id': 'swiss_international',
                                 'relation': 'visual_affinity', 'visual_reason': 'Grid'}],
                'notes': 'Preserve uncertainty',
            }
            self.records[cid] = record
            self.write_record(cid, record)

    def write_record(self, cid, record):
        (self.root / 'cases' / cid / 'case.json').write_text(
            json.dumps(record, ensure_ascii=False), encoding='utf-8')

    def test_exports_original_bytes_order_and_provenance_without_a_decision(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = stage(self.root, ['P-0002', 'P-0001', 'P-0002'], self.dest)
        manifest = json.loads((self.dest / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(result, manifest)
        self.assertEqual([x['id'] for x in manifest['items']], ['P-0002', 'P-0001'])
        self.assertEqual(manifest['purpose'], 'reference_candidates')
        self.assertIsNone(manifest['user_decision'])
        self.assertEqual(manifest['library_root'], str(self.root.resolve()))
        for item in manifest['items']:
            self.assertEqual(item['case'], self.records[item['id']])
            self.assertEqual(item['source_image_path'], self.records[item['id']]['image_path'])
            self.assertEqual((self.dest / item['staged_image_path']).read_bytes(), PNG)
            self.assertEqual(item['sha256'], hashlib.sha256(PNG).hexdigest())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()), ['images', 'manifest.json'])

    def test_invalid_ids_fail_before_creating_destination(self):
        for ids in ([], ['P-9999'], ['../P-0001'], ['P-0001', 'P-9999']):
            with self.subTest(ids=ids), self.assertRaises(StageError):
                stage(self.root, ids, self.dest)
            self.assertFalse(self.dest.parent.exists())

    def test_invalid_sources_fail_before_any_export(self):
        for image_path in ('../outside.png', str(self.base / 'outside.png'),
                           'cases/P-0002/missing.png', 'C:/outside.png'):
            record = copy.deepcopy(self.records['P-0002'])
            record['image_path'] = image_path
            self.write_record('P-0002', record)
            with self.subTest(path=image_path), self.assertRaises(StageError):
                stage(self.root, ['P-0001', 'P-0002'], self.dest)
            self.assertFalse(self.dest.parent.exists())

    def test_invalid_metadata_is_rejected(self):
        for record in ([], {'id': 'P-0002', 'image_path': 'cases/P-0001/preview.png'}):
            self.write_record('P-0001', record)
            with self.subTest(record=record), self.assertRaises(StageError):
                stage(self.root, ['P-0001'], self.dest)
        (self.root / 'cases/P-0001/case.json').write_text('{broken', encoding='utf-8')
        with self.assertRaises(StageError):
            stage(self.root, ['P-0001'], self.dest)
        self.assertFalse(self.dest.exists())

    def test_truncated_jpeg_fails_before_creating_output(self):
        record = copy.deepcopy(self.records['P-0001'])
        record['image_path'] = 'cases/P-0001/truncated.jpg'
        (self.root / record['image_path']).write_bytes(b'\xff\xd8')
        self.write_record('P-0001', record)
        with self.assertRaises(StageError):
            stage(self.root, ['P-0001'], self.dest)
        self.assertFalse(self.dest.parent.exists())

    def test_embedded_null_path_reports_a_concise_cli_error(self):
        record = copy.deepcopy(self.records['P-0001'])
        record['image_path'] = 'cases/P-0001/invalid\x00.png'
        self.write_record('P-0001', record)
        result = subprocess.run(
            [sys.executable, '-X', 'utf8', str(CLI), 'stage', '--root', str(self.root),
             '--ids', 'P-0001', '--dest', str(self.dest)],
            capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr + result.stdout)
        self.assertIn('ERROR:', result.stderr)
        self.assertFalse(self.dest.parent.exists())

    def test_existing_destination_and_source_subdirectory_are_untouched(self):
        self.dest.mkdir(parents=True)
        sentinel = self.dest / 'keep.txt'
        sentinel.write_text('keep', encoding='utf-8')
        for dest in (self.dest, self.root / 'new-staging', self.root):
            with self.subTest(dest=dest), self.assertRaises(StageError):
                stage(self.root, ['P-0001'], dest)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep')
        self.assertFalse((self.root / 'new-staging').exists())

    def test_copy_failure_does_not_publish_partial_output(self):
        import shutil
        real_copy = shutil.copy2
        calls = 0

        def fail_second(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('simulated disk failure')
            return real_copy(src, dst)

        with patch('staging.shutil.copy2', side_effect=fail_second), self.assertRaises(StageError):
            stage(self.root, ['P-0001', 'P-0002'], self.dest)
        self.assertFalse(self.dest.exists())
        self.assertEqual(list(self.dest.parent.iterdir()), [])

    def test_copy_mismatch_is_rejected(self):
        def corrupt_copy(src, dst):
            Path(dst).write_bytes(b'wrong')

        with patch('staging.shutil.copy2', side_effect=corrupt_copy), self.assertRaises(StageError):
            stage(self.root, ['P-0001'], self.dest)
        self.assertFalse(self.dest.exists())

    def test_escaping_image_symlink_is_rejected(self):
        external = self.base / 'outside.png'
        external.write_bytes(PNG)
        image = self.root / 'cases/P-0001/preview.png'
        image.unlink()
        try:
            image.symlink_to(external)
        except OSError as error:
            self.skipTest(f'Symlink creation unavailable: {error}')
        with self.assertRaises(StageError):
            stage(self.root, ['P-0001'], self.dest)

    def test_cli_exports_and_reports_expected_errors_without_tracebacks(self):
        base = [sys.executable, '-X', 'utf8', str(CLI), 'stage', '--root', str(self.root)]
        good = subprocess.run(base + ['--ids', 'P-0001', '--dest', str(self.dest)],
                              capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(good.returncode, 0, good.stderr + good.stdout)
        self.assertTrue((self.dest / 'images/P-0001.png').is_file())
        for arguments in ([], ['--ids', 'P-0001'],
                          ['--dest', str(self.dest)],
                          ['--ids', 'P-9999', '--dest', str(self.base / 'new')],
                          ['--ids', 'P-0001', '--dest', str(self.dest)]):
            bad = subprocess.run(base + arguments, capture_output=True, text=True, encoding='utf-8')
            with self.subTest(arguments=arguments):
                self.assertNotEqual(bad.returncode, 0)
                self.assertNotIn('Traceback', bad.stdout + bad.stderr)


if __name__ == '__main__':
    unittest.main()
