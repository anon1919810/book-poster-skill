"""Verify publication boundaries using real exports into temporary directories."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from library import validate
from release import FILES, ReleaseError, audit, digest, export, initialize, member, read_json, write_json
from test_retrieval import case
from test_staging import PNG


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='poster-release-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        self.root = self.repo / 'library'
        source = Path(__file__).resolve().parents[2]
        for relative in FILES:
            p = self.repo / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, p)
        for n in range(1, 3):
            cid = f'P-{n:04}'
            d = case(cid)
            d.update(taxonomy_version='0.2', annotation_status='draft',
                     source_url='https://example.org/' + cid, image_url='https://example.org/preview/' + cid,
                     image_path=f'cases/{cid}/preview.png', retrieved_at='2026-11-08',
                     source_evidence='Verified source', annotator='test', annotated_at='2026-11-08',
                     rights_note='No known restrictions on publication.')
            d['analysis'].update(failure_modes='No clutter', annotation_rationale='Test fixture')
            write_json(self.root / f'cases/{cid}/case.json', d)
            (self.root / d['image_path']).write_bytes(PNG if n == 1 else PNG + b'other')
        self.manifest = self.root / 'rights/release-manifest.json'
        initialize(self.root)
        self.dest = self.base / 'public'

    def approve(self):
        evidence = self.root / 'rights/evidence/P-0001.json'
        write_json(evidence, {'source': 'https://example.org/record', 'license': 'CC0-1.0'})
        data = read_json(self.manifest)
        data['cases'][0].update(image_status='approved', basis='CC0-1.0',
                               evidence_urls=['https://example.org/record'], verified_at=date.today().isoformat(),
                               reviewer='fixture-reviewer', attribution='Example work, test author',
                               attribution_required=False, notes='Explicit test fixture approval',
                               evidence_files=[{'path': 'rights/evidence/P-0001.json', 'sha256': digest(evidence)}])
        write_json(self.manifest, data)
        return data

    def test_initialization_never_approves_and_never_overwrites(self):
        self.assertEqual(audit(self.root)['statuses'], {'candidate': 2})
        with self.assertRaises(ReleaseError):
            initialize(self.root)
        with self.assertRaises(ReleaseError):
            export(self.repo, self.dest)
        self.assertFalse(self.dest.exists())

    def test_incomplete_approval_is_rejected(self):
        for key, value in [('evidence_urls', []), ('evidence_files', []), ('basis', None),
                           ('attribution_required', None), ('verified_at', '2026-02-30'),
                           ('reviewer', ''), ('image_sha256', '0' * 64)]:
            with self.subTest(key=key):
                data = self.approve()
                data['cases'][0][key] = value
                write_json(self.manifest, data)
                self.assertFalse(audit(self.root)['passed'])
                with self.assertRaises(ReleaseError):
                    export(self.repo, self.dest)
                self.assertFalse(self.dest.exists())

    def test_missing_duplicate_and_unknown_rows(self):
        original = read_json(self.manifest)
        for rows in [original['cases'][:1], original['cases'] + original['cases'][:1],
                     original['cases'] + [{'id': 'P-9999', 'image_status': 'approved'}]]:
            write_json(self.manifest, dict(schema_version=1, cases=rows))
            self.assertFalse(audit(self.root)['passed'])

    def test_changed_case_and_evidence_are_rejected(self):
        self.approve()
        path = self.root / 'rights/evidence/P-0001.json'
        path.write_text('{}', encoding='utf-8')
        self.assertFalse(audit(self.root)['passed'])
        self.approve()
        with (self.root / 'cases/P-0001/case.json').open('a', encoding='utf-8') as f:
            f.write('\n')
        self.assertFalse(audit(self.root)['passed'])

    def test_export_excludes_private_files_and_rebuilds(self):
        self.approve()
        (self.repo / '.git').mkdir()
        (self.repo / '.git/private').write_text('secret history', encoding='utf-8')
        (self.repo / 'skills/book-poster/library.local.json').write_text('private config', encoding='utf-8')
        (self.root / 'gallery.html').write_text('PRIVATE OLD GALLERY', encoding='utf-8')
        report = export(self.repo, self.dest)
        self.assertEqual(report['included_ids'], ['P-0001'])
        self.assertEqual(report['excluded_image_ids'], ['P-0002'])
        self.assertFalse((self.dest / '.git').exists())
        self.assertIn('MIT License', (self.dest / 'LICENSE').read_text(encoding='utf-8'))
        self.assertIn('not relicensed under MIT', (self.dest / 'LICENSE-SCOPE.md').read_text(encoding='utf-8'))
        self.assertFalse((self.dest / 'LICENSE-STATUS.md').exists())
        self.assertEqual(report['code_license'], 'MIT')
        self.assertNotIn('license_pending', report['status'])
        self.assertIn('* -text', (self.dest / '.gitattributes').read_text(encoding='utf-8'))
        self.assertFalse((self.dest / 'skills/book-poster/library.local.json').exists())
        self.assertFalse((self.dest / 'library/cases/P-0002').exists())
        self.assertNotIn('PRIVATE OLD GALLERY', (self.dest / 'library/gallery.html').read_text(encoding='utf-8'))
        catalog = read_json(self.dest / 'catalog.json')['cases']
        self.assertEqual([d['image_available'] for d in catalog], [True, False])
        self.assertNotIn('image_url', catalog[1])
        self.assertNotIn('analysis', catalog[1])
        self.assertEqual(validate(self.dest / 'library')[0], [])
        self.assertTrue(audit(self.dest / 'library')['passed'])
        for relative, expected in report['file_sha256'].items():
            self.assertEqual(digest(self.dest / relative), expected)
        rebuilt = subprocess.run([sys.executable, '-B', '-X', 'utf8', 'library/tools/library.py',
                                  'build', '--root', 'library'], cwd=self.dest,
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr + rebuilt.stdout)

    def test_existing_or_inside_destination_is_rejected(self):
        self.approve()
        self.dest.mkdir()
        for p in (self.dest, self.repo / 'output', self.base):
            with self.assertRaises(ReleaseError):
                export(self.repo, p)

    def test_traversal_and_link_are_rejected(self):
        for relative in ('../outside', '/outside', 'cases\\file', 'D' + ':/outside'):
            with self.assertRaises(ReleaseError):
                member(self.root, relative)
        target = self.root / 'outside-link'
        try:
            target.symlink_to(self.root / 'cases/P-0001/case.json')
        except OSError:
            self.skipTest('OS does not allow creating symlinks in this test environment')
        with self.assertRaises(ReleaseError):
            member(self.root, 'outside-link')

    def test_malformed_manifest_fails(self):
        for value in ([], {'schema_version': 9, 'cases': []}, {'schema_version': 1, 'cases': [None]}):
            write_json(self.manifest, value)
            with self.assertRaises(ReleaseError):
                audit(self.root)


if __name__ == '__main__':
    unittest.main()
