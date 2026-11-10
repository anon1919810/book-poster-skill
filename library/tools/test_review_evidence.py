"""Require evidence before accepting or counting a reviewed poster."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from library import build, validate
from test_retrieval import case
from test_staging import PNG


class ReviewEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='poster-review-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'cases/P-0001'
        self.folder.mkdir(parents=True)
        self.image = self.folder / 'preview.png'
        self.image.write_bytes(PNG)
        self.record = case('P-0001')
        self.record.update(taxonomy_version='0.2', image_path='cases/P-0001/preview.png',
                           source_url='https://example.org/record', image_url='https://example.org/image',
                           retrieved_at='2026-11-08', source_evidence='Source record inspected',
                           annotator='annotator', annotated_at='2026-11-08')
        self.record['analysis'].update(failure_modes='Keep text readable',
                                       annotation_rationale='Initial annotation')
        self.evidence = {'reviewer': 'independent-reviewer', 'reviewed_at': '2026-11-08',
                         'image_sha256': hashlib.sha256(PNG).hexdigest(),
                         'source_check': 'Confirmed title and creator against the work record',
                         'visual_check': 'Inspected the full local image and its composition',
                         'source_urls': ['https://example.org/record']}

    def check(self, record):
        (self.folder / 'case.json').write_text(json.dumps(record), encoding='utf-8')
        return validate(self.root)

    def test_status_flip_without_review_evidence_is_rejected(self):
        errors, _, _ = self.check(self.record)
        self.assertTrue(any('review' in error for error in errors), errors)

    def test_draft_without_review_evidence_keeps_existing_warning(self):
        self.record['annotation_status'] = 'draft'
        errors, warnings, _ = self.check(self.record)
        self.assertEqual(errors, [])
        self.assertTrue(any('not independently reviewed' in warning for warning in warnings))

    def test_complete_review_is_accepted_and_counted(self):
        self.record['review'] = self.evidence
        errors, warnings, cases = self.check(self.record)
        self.assertEqual((errors, warnings), ([], []))
        build(self.root, cases)
        self.assertIn('1 条已复核', (self.root / 'gallery.html').read_text(encoding='utf-8'))

    def test_missing_and_malformed_review_fields_are_rejected(self):
        invalid = [('reviewer', ' '), ('reviewed_at', '2026-02-30'),
                   ('reviewed_at', '20261108'), ('source_check', ''), ('visual_check', None),
                   ('source_urls', []), ('source_urls', ['javascript:alert(1)']),
                   ('source_urls', 'https://example.org/record'), ('image_sha256', 'invalid')]
        for key, value in invalid:
            with self.subTest(key=key, value=value):
                record = copy.deepcopy(self.record)
                record['review'] = dict(self.evidence, **{key: value})
                errors, _, _ = self.check(record)
                self.assertTrue(any('review.' + key in error for error in errors), errors)

    def test_stale_image_hash_is_rejected_and_not_counted(self):
        self.record['review'] = dict(self.evidence, image_sha256='0' * 64)
        errors, _, cases = self.check(self.record)
        self.assertTrue(any('review.image_sha256' in error for error in errors), errors)
        build(self.root, cases)
        self.assertIn('0 条已复核', (self.root / 'gallery.html').read_text(encoding='utf-8'))

    def test_gallery_does_not_count_status_only_review(self):
        build(self.root, [self.record])
        self.assertIn('0 条已复核', (self.root / 'gallery.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
