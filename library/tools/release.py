"""Audit redistribution decisions and export a fresh, allowlisted release candidate."""
import argparse
import collections
import copy
import hashlib
import html
import json
import re
import stat
from datetime import date
from pathlib import Path

from library import build, controlled_tokens, validate, valid_url

MANIFEST = 'rights/release-manifest.json'
STATUSES = {'unreviewed', 'candidate', 'approved', 'excluded'}
FILES = [
    '.gitignore', 'LICENSE', 'LICENSE-SCOPE.md', 'skills/book-poster/SKILL.md',
    'skills/book-poster/agents/openai.yaml',
    'skills/book-poster/library.local.example.json',
    *['skills/book-poster/references/' + name + '.md' for name in
      ('research', 'selection', 'library', 'production', 'typography', 'photocraft', 'delivery')],
    'library/taxonomy.md', 'library/GLOSSARY.md', 'library/RETRIEVAL-GUIDE.md',
    'library/PUBLIC-RELEASE.md',
    'library/tools/retrieval-browser.js',
    *['library/tools/' + name + '.py' for name in
      ('library', 'gallery', 'retrieval', 'staging', 'usage', 'release', 'test_library',
       'test_exploration', 'test_retrieval', 'test_review_evidence', 'test_staging', 'test_release')],
]


class ReleaseError(ValueError):
    """Reject incomplete release evidence or an unsafe export."""


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def no_links(path):
    """Reject symlinks and Windows junctions, including linked ancestors."""
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ReleaseError('Linked path: ' + str(part))
        if part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ReleaseError('Reparse point: ' + str(part))


def member(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ReleaseError('Invalid relative path')
    value = Path(relative)
    if value.is_absolute() or '..' in value.parts:
        raise ReleaseError('Path traversal')
    target = root / value
    no_links(target)
    if not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
        raise ReleaseError('Missing/outside file: ' + relative)
    return target


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_cases(root):
    no_links(root)
    records = {}
    for path in sorted((root / 'cases').glob('*/case.json')):
        member(root, path.relative_to(root).as_posix())
        data = read_json(path)
        cid = data.get('id')
        if not isinstance(cid, str) or not re.fullmatch(r'P-\d{4}', cid) or cid != path.parent.name or cid in records:
            raise ReleaseError('Invalid/duplicate case ID')
        member(root, data.get('image_path'))
        records[cid] = data
    if not records:
        raise ReleaseError('No cases found')
    return records


def initialize(root):
    target = root / MANIFEST
    no_links(target)
    if target.exists():
        raise ReleaseError('Manifest exists; review it rather than reinitializing')
    rows = []
    for cid, case in load_cases(root).items():
        note = case.get('rights_note', '')
        rows.append(dict(id=cid, image_sha256=digest(member(root, case['image_path'])),
                         case_sha256=digest(root / 'cases' / cid / 'case.json'),
                         image_status='candidate' if 'API marks' in note or 'No known restrictions' in note else 'unreviewed',
                         basis=None, evidence_urls=[], evidence_files=[], verified_at=None,
                         reviewer=None, attribution=None, attribution_required=None,
                         legacy_rights_note=note, notes='Legacy note is a lead, not redistribution approval.'))
    data = {'schema_version': 1, 'cases': rows}
    write_json(target, data)
    return data


def inspect(root):
    cases = load_cases(root)
    manifest = read_json(member(root, MANIFEST))
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or not isinstance(manifest.get('cases'), list):
        raise ReleaseError('Invalid manifest schema')
    rows, errors = {}, []
    for row in manifest['cases']:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise ReleaseError('Malformed manifest row')
        cid = row['id']
        if cid in rows or cid not in cases:
            errors.append(cid + ': duplicate/unknown ID')
            continue
        rows[cid] = row
        if row.get('image_status') not in STATUSES:
            errors.append(cid + ': invalid status')
        case = cases[cid]
        if row.get('image_sha256') != digest(member(root, case['image_path'])):
            errors.append(cid + ': image hash changed; re-review required')
        if row.get('case_sha256') != digest(root / 'cases' / cid / 'case.json'):
            errors.append(cid + ': case hash changed; re-review required')
        if row.get('image_status') != 'approved':
            continue
        for key in ('basis', 'reviewer', 'attribution', 'notes'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append(cid + ': missing ' + key)
        if type(row.get('attribution_required')) is not bool:
            errors.append(cid + ': attribution requirement must be explicit')
        try:
            stamp = row.get('verified_at')
            if not isinstance(stamp, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', stamp) or date.fromisoformat(stamp) > date.today():
                raise ValueError()
        except ValueError:
            errors.append(cid + ': invalid verification date')
        urls = row.get('evidence_urls')
        if not isinstance(urls, list) or not urls or not all(valid_url(u) for u in urls):
            errors.append(cid + ': evidence URLs required')
        evidence = row.get('evidence_files')
        if not isinstance(evidence, list) or not evidence:
            errors.append(cid + ': evidence files required')
        else:
            for record in evidence:
                try:
                    if not isinstance(record, dict) or digest(member(root, record.get('path'))) != record.get('sha256'):
                        raise ReleaseError('Evidence digest mismatch')
                except ReleaseError as exc:
                    errors.append(cid + ': ' + str(exc))
    errors.extend(cid + ': missing manifest row' for cid in cases.keys() - rows.keys())
    return cases, rows, errors


def audit(root):
    cases, rows, errors = inspect(root)
    return {'cases': len(cases), 'statuses': dict(collections.Counter(r.get('image_status') for r in rows.values())),
            'errors': errors, 'passed': not errors}


def clean_text(data):
    """Reject local paths and credential-shaped material in public text."""
    text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    patterns = (r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]', r'file://', r'/Users/', r'/home/',
                r'-----BEGIN .*PRIVATE KEY-----', r'github_pat_[A-Za-z0-9_]+', r'gh[pousr]_[A-Za-z0-9]{20,}')
    if any(re.search(pattern, text) for pattern in patterns):
        raise ReleaseError('Local path or credential-shaped material in public content')
    return data


def public_case(case, row):
    keys = ('id', 'title', 'creator', 'year', 'taxonomy_version', 'original_use', 'original_subjects',
            'source_url', 'image_url', 'image_path', 'image_sha256', 'retrieved_at', 'annotation_status',
            'annotator', 'annotated_at', 'art_history', 'observed', 'interpreted', 'techniques',
            'typography', 'color', 'analysis', 'review')
    result = {k: copy.deepcopy(case[k]) for k in keys if k in case}
    result['analysis'] = {key: value.strip() for key, value in result['analysis'].items()}
    result['rights_note'] = row['basis'] + '; see CREDITS.md and rights/release-manifest.json. ' + row['notes']
    result['source_evidence'] = 'Source record and local image identity were reviewed; see source_url and review.'
    result['notes'] = 'Release starter reference. Rights review is separate from visual/source review.'
    return clean_text(result)


def export(repo, dest):
    no_links(repo)
    no_links(dest)
    repo = repo.resolve()
    dest = dest.absolute()
    if dest.exists() or dest.resolve().is_relative_to(repo) or repo.is_relative_to(dest.resolve()):
        raise ReleaseError('Destination must be new and outside source repository')
    root = repo / 'library'
    cases, rows, errors = inspect(root)
    if errors:
        raise ReleaseError('\n'.join(errors))
    approved = [cid for cid in cases if rows[cid]['image_status'] == 'approved']
    if not approved:
        raise ReleaseError('No approved images; export would not be a usable starter')
    # Prepare all bytes and text before creating the destination; never copy whole trees.
    payload = {relative: member(repo, relative).read_bytes() for relative in FILES}
    for relative, raw in payload.items():
        # Code contains the scanner's own signatures and deliberate negative fixtures.
        # Its explicit allowlist is reviewed as code; scan documents and all data.
        if not relative.endswith('.py'):
            clean_text(raw.decode('utf-8-sig'))
    exported, public_rows = [], []
    for cid in approved:
        case, row = cases[cid], rows[cid]
        if not re.fullmatch(r'cases/' + re.escape(cid) + r'/preview\.(jpg|jpeg|png)', case['image_path']):
            raise ReleaseError(cid + ': approved image must be the case preview')
        data = public_case(case, row)
        raw = member(root, case['image_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['image_sha256']:
            raise ReleaseError(cid + ': image changed during export')
        payload['library/' + case['image_path']] = raw
        payload[f'library/cases/{cid}/case.json'] = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        exported.append(data)
        public_row = {key: copy.deepcopy(row[key]) for key in ('id', 'image_sha256', 'image_status', 'basis',
                      'evidence_urls', 'evidence_files', 'verified_at', 'reviewer', 'attribution', 'attribution_required', 'notes')}
        public_row['case_sha256'] = hashlib.sha256(payload[f'library/cases/{cid}/case.json']).hexdigest()
        for evidence in row['evidence_files']:
            # Evidence snapshots must themselves be small curated JSON, never raw source pages.
            if not re.fullmatch(r'rights/evidence/[A-Za-z0-9_-]+\.json', evidence['path']):
                raise ReleaseError('Evidence file must be a curated rights/evidence/*.json')
            evidence_raw = member(root, evidence['path']).read_bytes()
            clean_text(read_json(member(root, evidence['path'])))
            payload['library/' + evidence['path']] = evidence_raw
        public_rows.append(clean_text(public_row))
    catalog = [clean_text(dict(**{k: d.get(k) for k in ('id', 'title', 'creator', 'year', 'source_url')},
                              tags=sorted(controlled_tokens(d)), image_available=cid in approved))
               for cid, d in cases.items()]
    # A concurrent process must not turn the destination into an existing directory.
    dest.mkdir(parents=True, exist_ok=False)
    for relative, raw in payload.items():
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    write_json(dest / 'catalog.json', {'schema_version': 1, 'cases': catalog})
    (dest / '.gitattributes').write_bytes(
        b'# Preserve the exact bytes bound to rights evidence and release checksums.\n* -text\n')
    write_json(dest / 'library' / MANIFEST, {'schema_version': 1, 'cases': public_rows})
    errs, warnings, checked = validate(dest / 'library')
    if errs:
        raise ReleaseError('Candidate library failed validation: ' + '\n'.join(errs))
    build(dest / 'library', checked)
    credits = ['# Image credits', '', 'Per-image rights apply. Code/documentation licensing does not relicense these images.', '']
    for cid in approved:
        row = rows[cid]
        credits.extend([f'## {cid}', '', row['attribution'], '', f"Basis: {row['basis']}; reviewed {row['verified_at']}.",
                        '', 'Attribution required: ' + str(row['attribution_required']) + '.', '', row['notes'], '',
                        *['- ' + url for url in row['evidence_urls']], ''])
    (dest / 'CREDITS.md').write_text('\n'.join(credits), encoding='utf-8')
    (dest / 'README.md').write_text(
        '# Book Poster\n\n'
        'A Codex Skill for designing book posters from book research, real poster references, and iterative visual decisions.\n'
        'The workflow connects a book\'s argument or story to composition, typography, source materials, production, and refinement.\n\n'
        f'This package contains {len(approved)} reviewed starter images and {len(catalog)} minimal catalog records.\n'
        'Catalog-only records have source-page links, no bundled image and no promise of download/reuse permission.\n'
        'This is a historical starter, not the full private collection or a claim of balanced style coverage.\n\n'
        '## Quick start\n\n'
        'Open `library/gallery.html` to browse actual bundled references. `catalog.html` lists source-only entries too.\n'
        'Copy `skills/book-poster` into your Codex skills directory; configure its `library.local.json` with the absolute path to this library.\n'
        'The example relative path works when the Skill stays in this repository. You may point to your own library.\n'
        'Python 3.10+ is required for the tools; Pillow is optional for full image decoding.\n\n'
        'Ask Codex to use book-poster, name a book, and describe your audience. Open exploration shows at least four real references before choosing a direction.\n'
        'The Skill requires the host\'s own research and image tools; it does not include a model service or API keys. PhotoCraft is optional for editable native assets.\n\n'
        '```sh\npython -X utf8 library/tools/library.py validate --root library\n'
        'python -X utf8 library/tools/library.py search --root library --query "linework" --diverse --limit 4\n'
        'python -X utf8 library/tools/release.py audit --root library\n```\n\n'
        '## License\n\n'
        'Original code, Skill instructions, documentation, and original annotations are licensed under [MIT](LICENSE).\n'
        'Reference images retain their individual rights; see [license scope](LICENSE-SCOPE.md) and [image credits](CREDITS.md).\n'
        'The initial 17 bundled images carry the museum\'s public-domain/CC0 designation. Links to other works do not grant reuse permission.\n\n'
        'See `library/PUBLIC-RELEASE.md` for auditing and exporting a reviewed library. Local configurations, private reports, and generated user posters are excluded.\n', encoding='utf-8')
    (dest / 'library/README.md').write_text(
        '# Starter library\n\nBrowse gallery.html; case.json is the metadata source of truth.\n'
        'Only the images listed in ../CREDITS.md are bundled. ../catalog.json also lists source-only cases.\n'
        'Do not treat catalog-only records as images already viewed or staged.\n', encoding='utf-8')
    links = ''.join('<tr><td>' + html.escape(d['id']) + '</td><td><a href="' + html.escape(d['source_url'], quote=True)
                    + '">' + html.escape(d['title']) + '</a></td><td>' + ('Bundled' if d['image_available'] else 'Source link only')
                    + '</td></tr>' for d in catalog)
    (dest / 'catalog.html').write_text('<!doctype html><meta charset="utf-8"><title>Book Poster catalog</title>'
        '<h1>Reference catalog</h1><p><a href="library/gallery.html">Browse bundled images</a>. '
        'Source links do not grant reproduction permission.</p><table><tr><th>ID</th><th>Work</th><th>Availability</th></tr>'
        + links + '</table>', encoding='utf-8')
    hashes = {p.relative_to(dest).as_posix(): digest(p) for p in sorted(dest.rglob('*')) if p.is_file()}
    report = {'status': 'prepared_public_export', 'code_license': 'MIT', 'included_ids': approved,
              'excluded_image_ids': [cid for cid in cases if cid not in approved],
              'catalog_count': len(catalog), 'validation_warnings': warnings, 'file_sha256': hashes}
    write_json(dest / 'release-report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'audit', 'export'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--dest', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            output = {'initialized': len(initialize(args.root)['cases'])}
        elif args.command == 'audit':
            output = audit(args.root)
        else:
            if args.dest is None:
                raise ReleaseError('export requires --dest')
            report = export(args.repo, args.dest)
            output = {'included_images': len(report['included_ids']), 'catalog_count': report['catalog_count'], 'destination': str(args.dest)}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return int(bool(output.get('errors')))
    except (ReleaseError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, 'ERROR: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
