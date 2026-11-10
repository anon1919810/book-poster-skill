"""Explainable local poster retrieval; no external runtime dependencies."""
import json
import re
from functools import lru_cache
from pathlib import Path

FACETS = ('family', 'history', 'relation', 'composition', 'concept', 'driver', 'use', 'status')


def normalize_query(query, aliases):
    # Match whole words/phrases; only split a CJK token if EVERY part is known.
    # Otherwise 摄影师 must remain 摄影师, not photographic_editorial + 师.
    output = []
    cjk_keys = sorted((k for k in aliases if re.fullmatch(r'[\u3400-\u9fff]+', k)), key=lambda k: (-len(k), k))
    @lru_cache(None)
    def split_cjk(token):
        if not token: return ()
        for key in cjk_keys:
            if token.startswith(key):
                rest = split_cjk(token[len(key):])
                if rest is not None: return (aliases[key],) + rest
        return None
    phrase_width = max((len(k.split()) for k in aliases), default=1)
    for segment in re.split(r'[,，;；|]+', query.lower().strip()):
        tokens = segment.split(); pos = 0
        while pos < len(tokens):
            for width in range(min(phrase_width, len(tokens)-pos), 0, -1):
                phrase = ' '.join(tokens[pos:pos+width])
                if phrase in aliases:
                    output.append(aliases[phrase]); pos += width; break
            else:
                token = tokens[pos]
                parts = split_cjk(token) if re.fullmatch(r'[\u3400-\u9fff]+', token) else None
                output.extend(parts if parts is not None else [token]); pos += 1
    return list(dict.fromkeys(output))


def tie_key(case, seed, words):
    """Hash source AND work identity; several works can share one catalogue page."""
    identity = (case.get('source_url') or '') + '\0' + case['id']
    value = str(seed) + '\0' + '\0'.join(words) + '\0' + identity
    result = 2166136261
    for byte in value.encode('utf-8'):
        result = ((result ^ byte) * 16777619) & 0xffffffff
    return result


def fields_for(case):
    o = case['observed']; i = case['interpreted']; c = case['color']
    return {
        'observed.visual_family': [v for v in o['visual_family'].values() if v],
        'observed.visual_driver': [o['visual_driver']],
        'observed.composition': o['composition'],
        'observed.text_density': [o['text_density']],
        'interpreted.tone': i['tone'],
        'interpreted.transferable_concepts': [v['id'] for v in i['transferable_concepts']],
        'techniques': case['techniques'], 'typography': case['typography'],
        'color.color_mode': [c['color_mode']], 'color.color_contrast': [c['color_contrast']],
        'color.dominant_colors': c['dominant_colors'], 'original_use': [case['original_use']],
        'art_history.term_id': [v['term_id'] for v in case['art_history']],
        'art_history.relation': [v['relation'] for v in case['art_history']],
    }


def facet_values(case):
    return {
        'family': list(case['observed']['visual_family'].values()),
        'history': [h['term_id'] for h in case['art_history']],
        'relation': [h['relation'] for h in case['art_history']],
        'composition': case['observed']['composition'],
        'concept': [v['id'] for v in case['interpreted']['transferable_concepts']],
        'driver': [case['observed']['visual_driver']], 'use': [case['original_use']],
        'status': [case['annotation_status']],
    }


def passes_filters(case, filters):
    values = facet_values(case)
    for key, wanted in filters.items():
        if key not in FACETS: raise ValueError('Unknown filter: ' + key)
        if wanted and not any(v in values[key] for v in wanted): return False
    histories, relations = filters.get('history', []), filters.get('relation', [])
    if histories and relations:
        return any(h['term_id'] in histories and h['relation'] in relations for h in case['art_history'])
    return True


def text_fields(case):
    return {'id': case['id'], 'title': case.get('title') or '', 'creator': case.get('creator') or '',
            'year': case.get('year') or '', 'original_subjects': ' '.join(case['original_subjects']),
            'analysis': ' '.join(str(v) for k, v in case['analysis'].items() if k != 'annotation_rationale'),
            'concept_reasons': ' '.join(v.get('reason', '') for v in case['interpreted']['transferable_concepts'])}


def search(cases, query, aliases, controlled, match='any', filters=None, diverse=False, limit=8,
           seed='', usage_counts=None, batch_ids=None):
    if match not in ('any', 'all'): raise ValueError('match must be any or all')
    filters = {k: [aliases.get(v.lower(), v.lower()) for v in values] for k, values in (filters or {}).items()}
    words = normalize_query(query, aliases)
    usage_counts = usage_counts or {}
    batch_ids = set(batch_ids or [])
    batch_cases = [c for c in cases if c['id'] in batch_ids]
    candidates = []
    for case in cases:
        if not passes_filters(case, filters): continue
        structured, free = fields_for(case), text_fields(case)
        matched, field_names, score = [], set(), 0
        for word in words:
            if word in controlled:
                hits = [key for key, values in structured.items() if word in values]
                weight = 2
            else:
                hits = [key for key, text in free.items() if word in text.lower()]
                weight = 4 if any(k in hits for k in ('id', 'title', 'creator')) else 1
            if hits:
                matched.append(word); field_names.update(hits); score += weight
        if words and (not matched or match == 'all' and len(matched) != len(words)): continue
        counts = usage_counts.get(case['id'], {})
        shown, used = counts.get('shown', 0), counts.get('used', 0)
        batch_repeat = case['id'] in batch_ids
        # Bounded soft context: never exclude a relevant reference.
        context = min(shown, 4)*.25 + min(used, 4)*.5 + 2*batch_repeat
        batch_overlap = max((len(set(case['observed']['composition']) & set(c['observed']['composition']))
                             for c in batch_cases if c['id'] != case['id']), default=0)
        context += min(batch_overlap, 3)*.25
        row = {'id': case['id'], 'score': score, 'query_coverage': len(matched),
               'query_terms': list(words), 'missing_terms': [word for word in words if word not in matched],
               'matched_terms': matched, 'matched_fields': sorted(field_names),
               'family': case['observed']['visual_family']['primary'], 'creator': case.get('creator'),
               'seed': str(seed), 'recent_shown': shown, 'recent_used': used,
               'batch_repeat': batch_repeat, 'batch_composition_overlap': batch_overlap,
               'context_penalty': context, 'tie_break': tie_key(case, seed, words)}
        candidates.append((row, case))
    candidates.sort(key=lambda item: (-item[0]['query_coverage'], -item[0]['score'], item[0]['context_penalty'], item[0]['tie_break'], item[0]['id']))
    chosen = []
    while candidates and (limit is None or len(chosen) < max(0, limit)):
        if not diverse:
            chosen.append(candidates.pop(0)); continue
        coverage = candidates[0][0]['query_coverage']
        covered_terms = {term for row, _ in chosen for term in row['matched_terms']}
        def utility(item):
            row, case = item
            penalty = 0
            for prior, pc in chosen:
                penalty += 3 * bool(row['creator'] and row['creator'] == prior['creator'])
                penalty += 2 * bool(row['family'] and row['family'] == prior['family'])
                penalty += .25 * len(set(case['observed']['composition']) & set(pc['observed']['composition']))
            uncovered = sum(term not in covered_terms for term in row['matched_terms'])
            return (-uncovered, -row['score'], penalty + row['context_penalty'], row['tie_break'], row['id'])
        index = min((j for j, item in enumerate(candidates) if item[0]['query_coverage'] == coverage),
                    key=lambda j: utility(candidates[j]))
        chosen.append(candidates.pop(index))
    return [row for row, _ in chosen]


def browser_engine(aliases, controlled):
    config = json.dumps({'aliases': aliases, 'controlled': sorted(controlled)}, ensure_ascii=False).replace('<', '\\u003c')
    return 'const POSTER_SEARCH_CONFIG=' + config + ';\n' + Path(__file__).with_name('retrieval-browser.js').read_text(encoding='utf-8')
