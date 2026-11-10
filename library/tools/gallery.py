"""Static gallery with the same matching semantics as the CLI."""
import collections
import html
import json
from retrieval import browser_engine
from library import reviewed_evidence_errors


def render_gallery(cases, cards, aliases, controlled, names, relations, statuses, image_hashes=None):
    escape = lambda value: html.escape(str(value), quote=True)
    facet_paths = {
        'family': ('视觉路线', lambda c: list(c['observed']['visual_family'].values())),
        'history': ('艺术史', lambda c: [h['term_id'] for h in c['art_history']]),
        'relation': ('历史关系', lambda c: [h['relation'] for h in c['art_history']]),
        'composition': ('构图', lambda c: c['observed']['composition']),
        'concept': ('可迁移概念', lambda c: [x['id'] for x in c['interpreted']['transferable_concepts']]),
        'driver': ('视觉主体', lambda c: [c['observed']['visual_driver']]),
        'use': ('原始用途', lambda c: [c['original_use']]),
        'status': ('复核状态', lambda c: [c['annotation_status']]),
    }
    labels = {**names, **relations, **statuses}
    selectors = []
    for key, (title, values) in facet_paths.items():
        counts = collections.Counter(v for c in cases for v in set(values(c)) if v)
        options = ''.join(f'<option value="{escape(v)}">{escape(labels.get(v,v))} ({n})</option>' for v,n in sorted(counts.items()))
        selectors.append(f'<label>{title}<select id="f-{key}"><option value="">全部</option>{options}</select></label>')
    image_hashes = image_hashes or {}
    reviewed = sum(c['annotation_status']=='reviewed' and not reviewed_evidence_errors(c, image_hashes.get(c['id'])) for c in cases)
    payload = json.dumps(cases,ensure_ascii=False).replace('<','\\u003c')
    scripts = browser_engine(aliases, controlled) + '\nconst records=' + payload + ';\n' + r'''
const cards=[...document.querySelectorAll('article')];
const fieldKeys=['family','history','relation','composition','concept','driver','use','status'];
function filter(){
  const query=document.querySelector('#q').value;
  const filters=Object.fromEntries(fieldKeys.map(k=>[k,document.querySelector('#f-'+k)?.value]).filter(([,v])=>v).map(([k,v])=>[k,[v]]));
  const rows=PosterSearch.search(records,query,{match:document.querySelector('#match')?.value||'any',filters,diverse:!!document.querySelector('#diverse')?.checked,limit:null});
  const found=new Map(rows.map((r,i)=>[r.id,{r,i}]));
  cards.forEach((card,i)=>{const hit=found.get(records[i].id);card.hidden=!hit;
    if(card.style)card.style.order=hit?hit.i:records.length;
    const note=card.querySelector?.('.match-note');if(note)note.textContent=hit&&hit.r.matched_terms.length?'命中：'+hit.r.matched_terms.join('、')+(hit.r.missing_terms.length?'；未命中：'+hit.r.missing_terms.join('、'):''):'按当前筛选显示';});
  document.querySelector('#count').textContent=rows.length+' / '+records.length+' 张';
}
for(const id of ['q','match','diverse',...fieldKeys.map(k=>'f-'+k)]){
  const el=document.querySelector('#'+id);el?.addEventListener?.(id==='q'?'input':'change',filter);
}
filter();
'''
    # Existing cards include escaping and provenance links from library.build.
    with_notes = [card.replace('</article>','<p class="match-note"></p></article>') for card in cards]
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>POSTER LAB · 海报参考库</title>
<style>body{{background:#eee9df;color:#222;font:16px system-ui;margin:28px}}header{{max-width:1100px}}h1{{letter-spacing:.06em}}.controls{{background:#eee9df;padding:12px 0;display:flex;gap:10px;flex-wrap:wrap}}label{{display:flex;flex-direction:column;gap:4px;font-size:13px}}input,select{{font:inherit;padding:9px;border:1px solid #aaa;background:white;border-radius:3px}}#q{{width:min(700px,90vw)}}.switch{{flex-direction:row;align-items:center}}main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:22px;margin-top:24px}}article{{background:white;padding:16px;min-width:0}}img{{width:100%;height:360px;object-fit:contain}}h2{{font-size:18px;overflow-wrap:anywhere}}p{{line-height:1.6}}article[hidden]{{display:none}}.match-note{{font-size:12px;color:#555;overflow-wrap:anywhere}}a{{color:#245684}}select:focus,input:focus{{outline:2px solid #245684}}@media(max-width:500px){{body{{margin:15px}}img{{height:400px}}}}</style></head><body>
<header><h1>POSTER LAB</h1><p>真实海报参考库 · {len(cases)} 条 · {reviewed} 条已复核</p><p>以构图和视觉方法选图；流派关系与视觉近似分开。收藏参考不等于取得原图复用许可。</p></header>
<label>搜索作品、作者或视觉方法<input id="q" placeholder="例如：超现实主义 拼贴；或 Jan Tschichold"></label>
<div class="controls"><label>关键词关系<select id="match"><option value="any">任一命中 OR</option><option value="all">全部命中 AND</option></select></label>{''.join(selectors)}<label class="switch"><input type="checkbox" id="diverse">优先不同作者与构图</label></div>
<p id="count" aria-live="polite"></p><main>{''.join(with_notes)}</main><script>{scripts}</script></body></html>'''
