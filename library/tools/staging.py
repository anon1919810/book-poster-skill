"""Copy local reference candidates and provenance into a fresh task directory."""
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from library import inside


class StageError(ValueError):
    """Describe an actionable staging failure without publishing a partial result."""


def stage(root: Path, ids: list[str], destination: Path) -> dict:
    """Stage original images without altering the library or choosing a design.

    Args:
        root (Path): Existing canonical library directory.
        ids (list[str]): Explicit reference IDs, in presentation order.
        destination (Path): New task directory outside the library.

    Returns:
        (dict): The published manifest, including complete case snapshots.
    """
    root = Path(root).resolve()
    destination = Path(destination).absolute()
    if not root.is_dir():
        raise StageError(f'Library directory does not exist: {root}')
    if not ids:
        raise StageError('Provide at least one reference ID with --ids.')
    if destination.exists() or destination.is_symlink():
        raise StageError(f'Destination already exists; choose a new directory: {destination}')
    destination = destination.resolve()
    if destination.is_relative_to(root):
        raise StageError('Destination must be outside the source library.')

    items = []
    sources = []
    seen = set()
    for cid in ids:
        if not isinstance(cid, str) or not re.fullmatch(r'P-\d{4}', cid):
            raise StageError(f'Invalid reference ID: {cid!r}; expected P-0001 format.')
        if cid in seen:
            continue
        seen.add(cid)
        record_path = inside(root, f'cases/{cid}/case.json')
        if record_path is None or not record_path.is_file():
            raise StageError(f'Unknown reference or invalid record path: {cid}')
        try:
            record = json.loads(record_path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as error:
            raise StageError(f'Cannot read case {cid}: {error}') from error
        if not isinstance(record, dict) or record.get('id') != cid:
            raise StageError(f'Case ID does not match its directory: {cid}')
        try:
            source = inside(root, record.get('image_path'))
            if source is None or not source.is_file():
                raise StageError(f'Missing image or image path outside library: {cid}')
        except (OSError, ValueError, RuntimeError) as error:
            raise StageError(f'Invalid image path for {cid}: {error}') from error
        if source.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
            raise StageError(f'Unsupported image extension for {cid}: {source.suffix}')
        try:
            raw = source.read_bytes()
            jpeg = raw.startswith(b'\xff\xd8') and raw.endswith(b'\xff\xd9')
            png = raw.startswith(b'\x89PNG\r\n\x1a\n') and raw.endswith(b'IEND\xaeB`\x82')
            if not (jpeg or png):
                raise StageError(f'Invalid or truncated JPEG/PNG file: {cid}')
            digest = hashlib.sha256(raw).hexdigest()
        except OSError as error:
            raise StageError(f'Cannot read image {cid}: {error}') from error
        sources.append(source)
        items.append({
            'id': cid,
            'source_image_path': record['image_path'],
            'staged_image_path': f'images/{cid}{source.suffix}',
            'sha256': digest,
            'case': record,
        })

    manifest = {
        'schema_version': '1.0',
        'created_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'library_root': str(root),
        'purpose': 'reference_candidates',
        'user_decision': None,
        'items': items,
    }
    # All expected input failures precede mkdir/copy. Only our own scratch folder
    # is removed on failure; the destination is published after every copy verifies.
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.poster-stage-', dir=destination.parent) as temp:
            payload = Path(temp) / 'payload'
            (payload / 'images').mkdir(parents=True)
            for source, item in zip(sources, items):
                target = payload / item['staged_image_path']
                shutil.copy2(source, target)
                if hashlib.sha256(target.read_bytes()).hexdigest() != item['sha256']:
                    raise StageError(f'Copy verification failed for {item["id"]}; retry staging.')
            (payload / 'manifest.json').write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            if destination.exists() or destination.is_symlink():
                raise StageError(f'Destination appeared during staging; choose a new directory: {destination}')
            payload.rename(destination)
    except OSError as error:
        raise StageError(f'Could not publish staging directory {destination}: {error}') from error
    return manifest
