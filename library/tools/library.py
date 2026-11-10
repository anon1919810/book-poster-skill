"""Offline poster library, standard library runtime."""
import argparse,collections,hashlib,html,json,re,struct,zlib
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
ENUMS={
'family':'geometric_order expressive_type symbolic_reduction illustrative_organic photographic_editorial collage_montage surreal_concept ornamental_pattern diagrammatic_information material_experiment',
'driver':'type image symbol diagram balanced','composition':'centered asymmetric grid modular diagonal radial stacked split frame full_bleed negative_space repeating_field','density':'low medium high','tone':'restrained energetic dramatic playful solemn intimate mysterious rebellious','concept':'order aggregation dispersion connection growth conflict power transformation time memory identity exploration fragility cycle complexity contrast','techniques':'silhouette cutout flat_shapes linework geometric_repeat organic_curves photomontage paper_collage overprint halftone texture spatial_illusion','typography':'neutral_typesetting oversized condensed multidirectional hand_lettered custom_display integrated vertical_setting','mode':'achromatic limited_palette multicolor photographic','contrast':'strong soft mixed','colors':'black white gray red orange yellow green blue purple pink brown','history':'swiss_international futurism constructivism bauhaus de_stijl new_typography art_nouveau art_deco dada surrealism cubism pop_art psychedelic_graphics new_wave_graphics postmodern_graphics plakatstil','relation':'historical_affiliation documented_influence visual_affinity revival','use':'book_promotion exhibition performance film music_release event commercial public_message other'}
ALIASES={'瑞士国际主义':'swiss_international','瑞士风格':'swiss_international','swiss':'swiss_international','未来主义':'futurism','包豪斯':'bauhaus','构成主义':'constructivism','风格派':'de_stijl','新字体排印':'new_typography','新艺术':'art_nouveau','装饰艺术':'art_deco','达达':'dada','超现实主义':'surrealism','立体主义':'cubism','波普':'pop_art','迷幻':'psychedelic_graphics','新浪潮':'new_wave_graphics','后现代':'postmodern_graphics','德国海报风格':'plakatstil','几何':'geometric_order','摄影':'photographic_editorial','拼贴':'collage_montage','秩序':'order','聚合':'aggregation','冲突':'conflict','记忆':'memory'}
NAMES={'art_history': '艺术史', 'visual_family': '整体视觉路线，用于初筛与多样性', 'visual_driver': '主要靠什么吸引视线和传达信息', 'composition': '元素如何组织', 'text_density': '原作文字信息量', 'tone': '画面带来的表达气质', 'transferable_concepts': '可跨题材迁移的表达能力', 'swiss_international': '国际主义平面设计风格', 'futurism': '未来主义', 'constructivism': '构成主义', 'bauhaus': '包豪斯', 'de_stijl': '风格派', 'new_typography': '新字体排印', 'art_nouveau': '新艺术运动', 'art_deco': '装饰艺术', 'dada': '达达主义', 'surrealism': '超现实主义', 'cubism': '立体主义', 'pop_art': '波普艺术', 'psychedelic_graphics': '迷幻平面风格', 'new_wave_graphics': '新浪潮平面设计', 'postmodern_graphics': '后现代主义平面设计', 'plakatstil': '德国海报风格', 'historical_affiliation': '历史归属', 'documented_influence': '有据影响', 'visual_affinity': '视觉近似', 'revival': '当代复兴', 'geometric_order': '几何秩序', 'expressive_type': '表现性字体', 'symbolic_reduction': '符号凝练', 'illustrative_organic': '有机插画', 'photographic_editorial': '摄影叙事', 'collage_montage': '拼贴蒙太奇', 'surreal_concept': '超现实观念', 'ornamental_pattern': '装饰纹样', 'diagrammatic_information': '图解信息', 'material_experiment': '材质实验', 'type': '字体主导', 'image': '图像主导', 'symbol': '符号主导', 'diagram': '图解主导', 'balanced': '图文并重', 'centered': '中心聚焦', 'asymmetric': '不对称平衡', 'grid': '网格组织', 'modular': '模块分区', 'diagonal': '对角动势', 'radial': '放射环绕', 'stacked': '层叠堆积', 'split': '分割对照', 'frame': '框景包围', 'full_bleed': '满版延伸', 'negative_space': '留白聚焦', 'repeating_field': '重复铺陈', 'low': '低文字密度', 'medium': '中文字密度', 'high': '高文字密度', 'restrained': '克制', 'energetic': '活跃', 'dramatic': '戏剧性', 'playful': '诙谐', 'solemn': '庄重', 'intimate': '亲近', 'mysterious': '神秘', 'rebellious': '反叛', 'order': '秩序', 'aggregation': '聚合', 'dispersion': '分散', 'connection': '连接', 'growth': '生长', 'conflict': '冲突', 'power': '权力', 'transformation': '转变', 'time': '时间', 'memory': '记忆', 'identity': '身份', 'exploration': '探索', 'fragility': '脆弱', 'cycle': '循环', 'complexity': '复杂性', 'contrast': '对照', 'silhouette': '剪影', 'cutout': '抠图', 'flat_shapes': '平面色块', 'linework': '线描', 'geometric_repeat': '几何重复', 'organic_curves': '有机曲线', 'photomontage': '摄影拼合', 'paper_collage': '纸片拼贴', 'overprint': '叠印效果', 'halftone': '网点效果', 'texture': '材质纹理', 'spatial_illusion': '空间错觉', 'neutral_typesetting': '中性排字', 'oversized': '超大字形', 'condensed': '窄体字形', 'multidirectional': '多向排字', 'hand_lettered': '手写字形', 'custom_display': '定制展示字形', 'integrated': '图文融合', 'vertical_setting': '竖向编排'}
for _id, _name in NAMES.items():
    ALIASES[_name.lower()] = _id
for _terms in ENUMS.values():
    for _id in _terms.split(): ALIASES[_id] = _id
ALIASES.update({'国际主义平面设计风格':'swiss_international','国际字体风格':'swiss_international','swiss style':'swiss_international','international typographic style':'swiss_international','建构主义':'constructivism','新造型主义':'de_stijl','新字体运动':'new_typography','die neue typographie':'new_typography','jugendstil':'art_nouveau','sachplakat':'plakatstil'})
RELATIONS={'historical_affiliation':'历史归属','documented_influence':'有据影响','visual_affinity':'视觉近似','revival':'当代复兴／致敬'}
ALIASES.update({'瑞士主义':'swiss_international','international typographic style':'swiss_international',
    'the new typography':'new_typography','new typography':'new_typography','art nouveau':'art_nouveau',
    'art deco':'art_deco','de stijl':'de_stijl','pop art':'pop_art','psychedelic graphics':'psychedelic_graphics',
    'new wave graphic design':'new_wave_graphics','new wave graphics':'new_wave_graphics',
    'postmodern graphic design':'postmodern_graphics','postmodern graphics':'postmodern_graphics',
    'geometric order':'geometric_order','expressive typography':'expressive_type',
    'negative space':'negative_space','photographic editorial':'photographic_editorial',
    'surreal concept':'surreal_concept','material experiment':'material_experiment'})
STATUS={'draft':'初标','needs_review':'待复核','reviewed':'已复核'}
ALIASES.update({'瑞士':'swiss_international','留白':'negative_space','网格':'grid',
                '超现实':'surrealism','非对称':'asymmetric','对角线':'diagonal',
                '蒙太奇':'collage_montage','手写':'hand_lettered','满版':'full_bleed'})
def valid_url(value):
    if not isinstance(value,str): return False
    try:
        u=urlsplit(value)
        return u.scheme in ('http','https') and bool(u.hostname) and not any(c.isspace() for c in value)
    except ValueError: return False

def query_words(query):
    q=query.lower().strip()
    # Whole aliases can contain spaces; otherwise whitespace defines OR terms.
    return [ALIASES[q]] if q in ALIASES else [ALIASES.get(w,w) for w in q.split()]
CONTROLLED=set().union(*(set(v.split()) for v in ENUMS.values()))
def controlled_tokens(d):
    o=d['observed']; i=d['interpreted']; c=d['color']
    values=[*o['visual_family'].values(),o['visual_driver'],*o['composition'],o['text_density'],*i['tone'],*(x['id'] for x in i['transferable_concepts']),*d['techniques'],*d['typography'],c['color_mode'],c['color_contrast'],*c['dominant_colors'],d['original_use'],*(x['term_id'] for x in d['art_history']),*(x['relation'] for x in d['art_history'])]
    return {x for x in values if x is not None}
def free_text(d):
    values=[d.get(k) for k in ('id','title','creator','year','source_evidence','notes','rights_note')]
    values += d['original_subjects'] + list(d['analysis'].values())
    values += [x.get('reason','') for x in d['interpreted']['transferable_concepts']]
    values += [x.get(k,'') for x in d['art_history'] for k in ('evidence_note','visual_reason')]
    return ' '.join(str(v) for v in values if v is not None).lower()
def score_case(d, words):
    tokens=controlled_tokens(d); text=free_text(d)
    return sum((w in tokens) if w in CONTROLLED else (w in text) for w in words)
def family_matches(d, family):
    return not family or ALIASES.get(family.lower(),family) in d['observed']['visual_family'].values()

def inside(root,value):
    if not isinstance(value,str) or not value or Path(value).is_absolute() or re.match(r'^[A-Za-z]:',value) or '\\' in value:return None
    p=(root/value).resolve()
    return p if p.is_relative_to(root.resolve()) else None

def reviewed_evidence_errors(d, image_sha256=None):
    """Check review evidence against an independently computed image digest."""
    if d.get('annotation_status') != 'reviewed': return []
    review = d.get('review')
    if not isinstance(review, dict): return ['review must be an evidence object for reviewed cases']
    errors = []
    for key in ('reviewer', 'source_check', 'visual_check'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            errors.append('missing review.' + key)
    reviewed_at = review.get('reviewed_at')
    try:
        if not isinstance(reviewed_at, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', reviewed_at):
            raise ValueError('not an ISO date')
        date.fromisoformat(reviewed_at)
    except ValueError:
        errors.append('review.reviewed_at must be a valid YYYY-MM-DD date')
    digest = review.get('image_sha256')
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
        errors.append('invalid review.image_sha256')
    elif image_sha256 is None or digest.lower() != image_sha256:
        errors.append('review.image_sha256 does not match the current local image')
    urls = review.get('source_urls')
    if not isinstance(urls, list) or not urls or not all(valid_url(url) for url in urls):
        errors.append('review.source_urls must contain valid http(s) URLs')
    return errors

def validate(root):
    errors=[];warnings=[];cases=[];ids=set();hashes={}
    def err(cid,msg): errors.append(f'{cid}: {msg}')
    def enum(cid,val,kind):
        if val is not None and val not in ENUMS[kind].split():err(cid,f'invalid {kind}: {val}')
    def many(cid,vals,kind,limit):
        if not isinstance(vals,list):err(cid,f'{kind} must be list');return
        if len(vals)>limit or len(set(str(v) for v in vals))!=len(vals):err(cid,f'{kind} cardinality')
        for v in vals:
            if not isinstance(v,str):err(cid,f'invalid {kind} item type')
            else:enum(cid,v,kind)
    for file in sorted((root/'cases').glob('*/case.json')):
        try:
            d=json.loads(file.read_text(encoding='utf-8-sig'));cid=d.get('id',str(file));cases.append(d)
            if cid in ids:err(cid,'duplicate id')
            ids.add(cid)
            if not re.fullmatch(r'P-\d{4}',cid) or file.parent.name!=cid:err(cid,'ID/path mismatch')
            for key in ['title','source_url','image_url','retrieved_at','rights_note','source_evidence','annotator','annotated_at']:
                if not isinstance(d.get(key),str) or not d[key].strip():err(cid,f'missing {key}')
            for key in ['source_url','image_url']:
                if not valid_url(d.get(key)):err(cid,f'invalid URL {key}')
            for key in ['creator','year','notes']:
                if d.get(key) is not None and not isinstance(d.get(key),str):err(cid,f'invalid type {key}')
            if not isinstance(d.get('original_subjects'),list) or not all(isinstance(x,str) for x in d['original_subjects']):err(cid,'invalid original_subjects')
            for key in ['creator','year','original_use','original_subjects','art_history','techniques','typography','analysis','color','observed','interpreted','notes']:
                if key not in d:err(cid,f'missing {key}')
            if d.get('taxonomy_version')!='0.2':err(cid,'taxonomy version')
            if d.get('annotation_status') not in ['draft','needs_review','reviewed']:err(cid,'annotation status')
            elif d['annotation_status']!='reviewed':warnings.append(f'{cid}: {d["annotation_status"]}, not independently reviewed')
            enum(cid,d.get('original_use'),'use')
            sha=None
            p=inside(root,d.get('image_path'))
            if p is None or not p.is_file():err(cid,'invalid or missing image path')
            else:
                raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
                if sha in hashes:err(cid,'duplicate image '+hashes[sha])
                hashes[sha]=cid
                if not (raw.startswith(b'\xff\xd8') and raw.endswith(b'\xff\xd9') or raw.startswith(b'\x89PNG\r\n\x1a\n')):err(cid,'invalid image signature')
                try:
                    from PIL import Image
                    with Image.open(p) as im:im.verify()
                except ImportError:warnings.append(f'{cid}: decoder unavailable; image signature only')
                except Exception as ex:err(cid,'image decode: '+str(ex))
            for message in reviewed_evidence_errors(d, sha):err(cid, message)
            o=d['observed'];fam=o['visual_family'];enum(cid,fam['primary'],'family');enum(cid,fam.get('secondary'),'family')
            if fam['primary'] and fam['primary']==fam.get('secondary'):err(cid,'duplicate family')
            enum(cid,o['visual_driver'],'driver');many(cid,o['composition'],'composition',3);enum(cid,o['text_density'],'density')
            many(cid,d['interpreted']['tone'],'tone',2)
            concepts=d['interpreted']['transferable_concepts']
            if not isinstance(concepts,list):raise ValueError('transferable_concepts must be list')
            if len(concepts)>3 or len({x['id'] for x in concepts})!=len(concepts):err(cid,'concept cardinality')
            for x in concepts:
                enum(cid,x['id'],'concept')
                if not isinstance(x.get('reason'),str) or not x['reason'].strip():err(cid,'missing concept reason')
            for key in ['techniques','typography']:many(cid,d[key],key,3)
            c=d['color'];enum(cid,c['color_mode'],'mode');enum(cid,c['color_contrast'],'contrast');many(cid,c['dominant_colors'],'colors',3)
            if not isinstance(d['art_history'],list):raise ValueError('art_history must be list')
            if len({x.get('term_id') for x in d['art_history']})!=len(d['art_history']):err(cid,'duplicate history')
            for x in d['art_history']:
                enum(cid,x.get('term_id'),'history');enum(cid,x.get('relation'),'relation')
                if x.get('term_id') is None or x.get('relation') is None:err(cid,'null history term or relation')
                if x.get('source_url') is not None and not valid_url(x['source_url']):err(cid,'invalid history URL')
                if x.get('relation')=='visual_affinity':
                    if not isinstance(x.get('visual_reason'),str) or not x['visual_reason'].strip():err(cid,'missing visual reason')
                elif not all(x.get(k) for k in ['source_url','evidence_note','evidence_scope']):err(cid,'missing historical evidence')
                elif x.get('evidence_scope') not in ['work','creator']:err(cid,'invalid evidence scope')
            for key,x in d.get('adaptation',{}).items():
                if key not in ['long_title','han_typesetting','dense_copy'] or x.get('assessment') not in ['low_rework','medium_rework','high_rework','unknown'] or x.get('basis') not in ['inferred','tested'] or not x.get('reason'):err(cid,'invalid adaptation')
                if x.get('basis')=='tested':
                    record=inside(root,x.get('test_record'))
                    if record is None or not record.is_file():err(cid,'tested without record')
            for key in ['visual_mechanism','transferable_method','failure_modes','annotation_rationale']:
                if not d['analysis'].get(key):err(cid,'missing analysis '+key)
        except Exception as ex:errors.append(f'{file}: malformed case: {ex}')
    return errors,warnings,cases

def build(root,cases):
    compact=[];cards=[];image_hashes={}
    families={x:0 for x in ENUMS['family'].split()}
    histories={x:{r:0 for r in ENUMS['relation'].split()} for x in ENUMS['history'].split()}
    e=lambda s:html.escape(str(s),quote=True)
    label=lambda x:NAMES.get(x,x) if x else '未确定'
    for d in cases:
        cid=d['id'];fam=d['observed']['visual_family']
        if d.get('annotation_status')=='reviewed':
            image=inside(root,d.get('image_path'))
            if image is not None and image.is_file():
                image_hashes[cid]=hashlib.sha256(image.read_bytes()).hexdigest()
        if fam['primary'] is not None: families[fam['primary']]+=1
        for h in d['art_history']:histories[h['term_id']][h['relation']]+=1
        history='；'.join(label(x['term_id'])+'（'+RELATIONS[x['relation']]+'）' for x in d['art_history']) or '未确定'
        tags='、'.join(label(x) for x in [fam['primary'],fam.get('secondary')] if x) or '未确定'
        item={k:d.get(k) for k in ['id','title','creator','year','image_path','source_url','annotation_status']};item.update(art_history=d['art_history'],observed=d['observed'],interpreted={'tone':d['interpreted']['tone'],'transferable_concepts':[x['id'] for x in d['interpreted']['transferable_concepts']]},techniques=d['techniques'],typography=d['typography'],color=d['color'],original_use=d['original_use']);compact.append(item)
        searchable=free_text(d); hist=json.dumps(sorted(controlled_tokens(d)))
        cards.append(f'<article data-search="{e(searchable)}" data-tokens="{e(hist)}"><img loading="lazy" src="{e(d["image_path"])}" alt="{e(d["title"])}"><h2>{e(cid)} · {e(d["title"])}</h2><p>{e(d["creator"])} / {e(d["year"])}</p><p>视觉路线：{e(tags)}<br>艺术史：{e(history)}<br>状态：{e(STATUS[d["annotation_status"]])}</p><p>{e(d["analysis"]["visual_mechanism"])}</p><a href="{e(d["source_url"])}">来源记录</a> · <a href="cases/{e(cid)}/case.md">完整案例</a></article>')
        md=f"# {d['title']}\n\n自动生成；以 case.json 为准。\n\n![原图](preview{Path(d['image_path']).suffix})\n\n## 元数据\n\n- 编号：{cid}\n- 作者：{d['creator']}\n- 年份：{d['year']}\n- 原用途：{d['original_use']}\n- 状态：{STATUS[d['annotation_status']]}\n\n## 标签\n\n- 视觉路线：{tags}\n- 艺术史：{history}\n- 构图：{ '、'.join(label(x) for x in d['observed']['composition'])}\n\n"
        o=d['observed']; i=d['interpreted']; c=d['color']
        md+=f"- 视觉主体：{label(o['visual_driver'])}\n- 文字密度：{label(o['text_density'])}\n- 气质：{', '.join(label(x) for x in i['tone']) or '未确定'}\n- 表现手法：{', '.join(label(x) for x in d['techniques']) or '未确定'}\n- 文字处理：{', '.join(label(x) for x in d['typography']) or '未确定'}\n- 色彩：{label(c['color_mode'])} / {label(c['color_contrast'])} / {', '.join(label(x) for x in c['dominant_colors'])}\n\n### 可迁移概念及依据\n\n"
        for x in i['transferable_concepts']:md+=f"- {label(x['id'])}：{x['reason']}\n"
        md+='\n### 艺术史关系及依据\n\n'
        for x in d['art_history']:
            reason=x.get('visual_reason') or x.get('evidence_note','')
            source=x.get('source_url')
            md+=f"- {label(x['term_id'])}（{RELATIONS[x['relation']]}）：{reason}"
            if source:md+=f"；[依据来源]({source})（{x.get('evidence_scope','')}）"
            md+='\n'
        md+='\n'
        md+='## 分析\n\n'
        for key,name in [('visual_mechanism','视觉机制'),('transferable_method','可迁移方法'),('failure_modes','失败风险'),('annotation_rationale','标注依据')]:md+=f"**{name}：** {d['analysis'][key]}\n\n"
        md+=f"## 来源\n\n- [作品记录]({d['source_url']})\n- [图片来源]({d['image_url']})\n- 来源证据：{d['source_evidence']}\n- 权利：{d['rights_note']}\n- 备注：{d['notes']}\n"
        (root/'cases'/cid/'case.md').write_text(md,encoding='utf-8')
    (root/'index.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in compact),encoding='utf-8')
    coverage={'total':len(cases),'visual_family':families,'art_history':histories,'gaps':{'visual_family':[k for k,v in families.items() if not v],'art_history':[k for k,v in histories.items() if not sum(v.values())]},'annotation_status':dict(collections.Counter(d['annotation_status'] for d in cases))}
    (root/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    from gallery import render_gallery
    (root/'gallery.html').write_text(render_gallery(cases,cards,ALIASES,CONTROLLED,NAMES,RELATIONS,STATUS,image_hashes=image_hashes),encoding='utf-8')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=['build','validate','search','test','stage','record-usage'])
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--query',default='');ap.add_argument('--limit',type=int,default=8)
    def enum_arg(kind):
        def parse(value):
            result=ALIASES.get(value.lower(),value.lower())
            if result not in ENUMS[kind].split():raise argparse.ArgumentTypeError('Unknown '+kind+': '+value)
            return result
        return parse
    ap.add_argument('--family',type=enum_arg('family'))
    for name,kind in [('history','history'),('relation','relation'),('composition','composition'),('concept','concept')]:
        ap.add_argument('--'+name,action='append',type=enum_arg(kind))
    ap.add_argument('--driver',type=enum_arg('driver'));ap.add_argument('--use',type=enum_arg('use'))
    ap.add_argument('--status',choices=list(STATUS))
    ap.add_argument('--match',choices=['any','all'],default='any')
    ap.add_argument('--diverse',action='store_true')
    ap.add_argument('--seed',default='',help='Reproducible task seed for equal-relevance exploration')
    ap.add_argument('--usage-ledger',type=Path,help='Optional explicit JSONL task usage ledger (not art history)')
    ap.add_argument('--recent-tasks',type=int,default=20,help='Distinct recent tasks to consider; 0 disables recency')
    ap.add_argument('--batch-ids',nargs='*',default=[],help='References already selected in this batch; soft penalty only')
    ap.add_argument('--event',type=Path,help='Usage event JSON file for record-usage')
    ap.add_argument('--ids',nargs='+',help='Explicit reference IDs to stage, in order')
    ap.add_argument('--dest',type=Path,help='New task staging directory outside the library')
    args=ap.parse_args()
    if args.command=='test':
        from test_library import run_tests
        run_tests(validate);return 0
    if args.command=='stage':
        if not args.ids or args.dest is None:ap.error('stage requires --ids and --dest')
        from staging import StageError,stage
        try:manifest=stage(args.root,args.ids,args.dest)
        except StageError as error:ap.exit(1,f'ERROR: {error}\n')
        print(f'Staged {len(manifest["items"])} original images; user decision remains unset.')
        print(str(args.dest.resolve()/'manifest.json'));return 0
    errors,warnings,cases=validate(args.root)
    if args.command=='validate':
        for x in errors:print('ERROR',x)
        for x in warnings:print('WARNING',x)
        print(f'{len(cases)} cases; {len(errors)} errors; {len(warnings)} warnings');return int(bool(errors))
    if errors:
        for x in errors:print('ERROR',x)
        return 1
    if args.command=='build':build(args.root,cases);print(f'Built {len(cases)} cases');return 0
    from usage import UsageError,load_events,usage_counts,record_event
    known_ids={d['id'] for d in cases}
    try:
        if args.command=='record-usage':
            if args.usage_ledger is None or args.event is None:ap.error('record-usage requires --usage-ledger and --event')
            event=json.loads(args.event.read_text(encoding='utf-8-sig'))
            changed=record_event(args.usage_ledger,event,known_ids)
            print('Recorded usage event' if changed else 'Usage event already recorded');return 0
        if set(args.batch_ids)-known_ids:raise UsageError('Unknown --batch-ids')
        events=load_events(args.usage_ledger,known_ids) if args.usage_ledger else []
        counts=usage_counts(events,args.recent_tasks)
    except (UsageError,OSError,UnicodeError,json.JSONDecodeError) as error:ap.exit(1,f'ERROR: {error}\n')
    from retrieval import search
    filters={}
    for name in ('family','history','relation','composition','concept','driver','use','status'):
        value=getattr(args,name)
        if value:filters[name]=value if isinstance(value,list) else [value]
    rows=search(cases,args.query,ALIASES,CONTROLLED,match=args.match,filters=filters,diverse=args.diverse,limit=args.limit,
                seed=args.seed,usage_counts=counts,batch_ids=args.batch_ids)
    lookup={d['id']:d for d in cases}
    for row in rows:
        d=lookup[row['id']]
        result={k:d[k] for k in ['id','title','image_path','source_url','art_history']}
        result.update(row)
        print(json.dumps(result,ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
