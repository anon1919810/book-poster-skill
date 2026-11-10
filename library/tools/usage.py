"""Explicit task reference usage; searches never write and the coordinator is sole writer."""
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path


class UsageError(ValueError):
    pass


def validate_event(event, known_ids=None):
    if not isinstance(event, dict): raise UsageError('Usage event must be an object')
    required = {'event_id', 'task_id', 'timestamp', 'shown_ids', 'used_ids'}
    if not required <= event.keys(): raise UsageError('Usage event missing required fields')
    if event.keys() - required - {'route_skeletons', 'note'}: raise UsageError('Unknown usage event fields')
    for key in ('event_id', 'task_id', 'timestamp'):
        if not isinstance(event[key], str) or not event[key].strip(): raise UsageError('Invalid ' + key)
    try:
        stamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        if stamp.tzinfo is None: raise ValueError('timezone required')
    except ValueError as error: raise UsageError('Timestamp must be ISO 8601 with timezone') from error
    def check_ids(ids):
        if not isinstance(ids, list) or any(not isinstance(i, str) or not re.fullmatch(r'P-\d{4}', i) for i in ids):
            raise UsageError('Reference IDs must be a list of P-NNNN strings')
        if len(set(ids)) != len(ids): raise UsageError('Duplicate reference ID in event')
        if known_ids is not None and set(ids)-set(known_ids): raise UsageError('Unknown reference IDs: ' + ', '.join(sorted(set(ids)-set(known_ids))))
    for key in ('shown_ids', 'used_ids'): check_ids(event[key])
    if 'note' in event and not isinstance(event['note'], str): raise UsageError('note must be text')
    routes = event.get('route_skeletons', [])
    if not isinstance(routes, list): raise UsageError('route_skeletons must be a list')
    for route in routes:
        if not isinstance(route, dict) or set(route) != {'route_id', 'reference_ids', 'description'}: raise UsageError('Invalid route skeleton')
        if any(not isinstance(route[k], str) or not route[k].strip() for k in ('route_id', 'description')): raise UsageError('Invalid route description')
        check_ids(route['reference_ids'])
    return event


def load_events(path, known_ids=None):
    path = Path(path)
    if not path.exists(): return []
    events, seen = [], {}
    try:
        for number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            if not line.strip(): continue
            try: event = validate_event(json.loads(line), known_ids)
            except (ValueError, TypeError) as error: raise UsageError(f'Invalid ledger {path}, line {number}: {error}') from error
            key = event['event_id']
            if key in seen:
                if seen[key] != event: raise UsageError('Conflicting event_id: ' + key)
                continue
            seen[key] = event; events.append(event)
    except (OSError, UnicodeError) as error: raise UsageError(f'Cannot read ledger {path}: {error}') from error
    return events


def usage_counts(events, recent_tasks=20):
    if isinstance(recent_tasks, bool) or not isinstance(recent_tasks, int) or recent_tasks < 0: raise UsageError('recent_tasks must be a nonnegative integer')
    tasks = list(dict.fromkeys(event['task_id'] for event in reversed(events)))[:recent_tasks]
    result = {}
    for task in tasks:
        selected = [e for e in events if e['task_id'] == task]
        shown = set(i for e in selected for i in e['shown_ids'])
        used = set(i for e in selected for i in e['used_ids'])
        for cid in shown | used:
            counts = result.setdefault(cid, {'shown': 0, 'used': 0})
            counts['shown'] += int(cid in shown); counts['used'] += int(cid in used)
    return result


def record_event(path, event, known_ids=None):
    """Idempotent and atomic replacement, not a multi-writer database."""
    validate_event(event, known_ids)
    path = Path(path); events = load_events(path, known_ids)
    for previous in events:
        if previous['event_id'] == event['event_id']:
            if previous == event: return False
            raise UsageError('Conflicting event_id: ' + event['event_id'])
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in [*events, event])
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as handle:
            temp = Path(handle.name); handle.write(content); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists(): temp.unlink()
    return True
