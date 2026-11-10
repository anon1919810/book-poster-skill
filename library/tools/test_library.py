import copy, json, tempfile, base64, subprocess, sys, re, html, shutil
from pathlib import Path

def run_tests(validate):
    from library import score_case,query_words,family_matches,build
    seed={'id':'P-0001','taxonomy_version':'0.2','title':'Example','creator':None,'year':None,'original_use':None,'original_subjects':[], 'source_url':'https://example.org/record','image_url':'https://example.org/image','retrieved_at':'2026-11-08','rights_note':'unknown','source_evidence':'record','annotation_status':'draft','annotator':'test','annotated_at':'2026-11-08','art_history':[],'observed':{'visual_family':{'primary':'geometric_order','secondary':'collage_montage'},'visual_driver':'type','composition':[],'text_density':'low'},'interpreted':{'tone':[],'transferable_concepts':[{'id':'order','reason':'pattern'}]},'techniques':[],'typography':[],'color':{'color_mode':'achromatic','color_contrast':'strong','dominant_colors':[]},'analysis':{'visual_mechanism':'x','transferable_method':'x','failure_modes':'x','annotation_rationale':'x'},'notes':'不是瑞士国际主义 swiss_international'}
    assert score_case(seed,query_words('瑞士国际主义'))==0
    assert score_case(seed,query_words('几何秩序'))==1
    assert score_case(seed,query_words('未来主义 几何秩序'))==1
    assert family_matches(seed,'拼贴蒙太奇')
    absent=copy.deepcopy(seed); absent['observed']['visual_driver']='symbol'; absent['notes']='type image order geometric_order'; absent['interpreted']['transferable_concepts']=[]; absent['observed']['visual_family']={'primary':'expressive_type','secondary':None}
    for word in ('字体主导','图像主导','秩序','几何秩序'):
        assert score_case(absent,query_words(word))==0, word
    assert score_case(seed,query_words('字体主导'))==1
    assert score_case(seed,query_words('图像主导'))==0
    assert score_case(seed,query_words('秩序'))==1
    assert not family_matches(absent,'几何秩序')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); p=root/'cases/P-0001'; p.mkdir(parents=True)
        (p/'preview.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='))
        seed['image_path']='cases/P-0001/preview.png'
        def check(data,expected):
            (p/'case.json').write_text(json.dumps(data),encoding='utf-8')
            errors,warnings,cases=validate(root)
            assert bool(errors)==expected,errors
        check(seed,False)
        for mutate in [lambda d:d.update(source_url='javascript:alert(1)'),lambda d:d.update(image_url='https:///missing'),lambda d:d.update(art_history=[{'term_id':None,'relation':'visual_affinity','visual_reason':'x'}]),lambda d:d.update(art_history=[{'term_id':'futurism','relation':None,'source_url':'https://example.org','evidence_note':'x','evidence_scope':'work'}]),lambda d:d.update(art_history=[{'term_id':'futurism','relation':'historical_affiliation','source_url':'javascript:bad','evidence_note':'x','evidence_scope':'work'}]),lambda d:d.update(image_path='../outside.png'),lambda d:d['observed'].update(visual_driver='bogus'),lambda d:d.update(source_evidence=''),lambda d:d['interpreted']['transferable_concepts'][0].update(reason=''),lambda d:d.update(art_history=[{'term_id':'futurism','relation':'historical_affiliation'}]),lambda d:d.update(adaptation={'long_title':{'assessment':'low_rework','basis':'tested','reason':'x','test_record':'absent.txt'}})]:
            bad=copy.deepcopy(seed);mutate(bad);check(bad,True)
        check(seed,False)
        unknown=copy.deepcopy(seed)
        unknown['observed']['visual_family']={'primary':None,'secondary':None}
        unknown['annotation_status']='needs_review'
        check(unknown,False)
        build(root,[unknown])
        unknown_coverage=json.loads((root/'coverage.json').read_text(encoding='utf-8'))
        assert sum(unknown_coverage['visual_family'].values())==0
        assert '视觉路线：未确定' in (root/'gallery.html').read_text(encoding='utf-8')
        check(seed,False)
        build(root,[seed]); coverage=json.loads((root/'coverage.json').read_text(encoding='utf-8'))
        assert len(coverage['art_history'])==16 and len(coverage['visual_family'])==10
        assert 'futurism' in coverage['gaps']['art_history']
        assert '视觉路线' in (root/'gallery.html').read_text(encoding='utf-8')
        gallery=(root/'gallery.html').read_text(encoding='utf-8')
        assert '视觉主体' in (p/'case.md').read_text(encoding='utf-8')
        index=json.loads((root/'index.jsonl').read_text(encoding='utf-8').splitlines()[0]); assert 'observed' in index and 'interpreted' in index
        # Execute the actual generated filtering script with a tiny DOM stub when Node is present.
        node=shutil.which('node')
        if node:
            attrs=re.search(r'<article data-search="([^"]*)" data-tokens="([^"]*)"',gallery)
            search,tokens=map(html.unescape,attrs.groups()); script=re.search(r'<script>(.*?)</script>',gallery,re.S).group(1)
            for query in ('字体主导 图像主导','未来主义 几何秩序','图像主导','秩序'):
                pre='const card={dataset:'+json.dumps({'search':search,'tokens':tokens})+',hidden:false};const input={value:'+json.dumps(query,ensure_ascii=False)+',addEventListener(){}};const count={};const document={querySelectorAll(){return [card]},querySelector(s){return s==="#q"?input:count}};'
                js=pre+script+';process.stdout.write(String(!card.hidden))'
                shown=subprocess.check_output([node,'-e',js],text=True)=='true'
                cmd=[sys.executable,str(Path(__file__).with_name('library.py')),'search','--root',str(root),'--query',query]
                cli=bool(subprocess.check_output(cmd,text=True,encoding='utf-8').strip())
                assert shown==cli,(query,shown,cli)
        q=root/'cases/P-0002';q.mkdir();(q/'case.json').write_text(json.dumps(seed),encoding='utf-8')
        errors,_,_=validate(root); assert any('duplicate id' in e for e in errors);assert any('duplicate image' in e for e in errors)
    with tempfile.TemporaryDirectory() as tmp:
        assert validate(Path(tmp))[:2]==([],[])
    print('PASS: valid, empty, traversal, enum, evidence, concept, tested record, duplicate IDs/images')

if __name__=='__main__':
    from library import validate
    run_tests(validate)
