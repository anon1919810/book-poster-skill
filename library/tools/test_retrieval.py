import copy
import shutil
import json
import subprocess
import unittest
from pathlib import Path

from retrieval import normalize_query, search, browser_engine


def case(cid, family='geometric_order', creator='A', history=None):
    return {'id': cid, 'title': 'Example', 'creator': creator, 'year': '1955',
            'original_use': 'exhibition', 'original_subjects': ['music'],
            'annotation_status': 'reviewed', 'art_history': history or [],
            'observed': {'visual_family': {'primary': family, 'secondary': None},
                         'composition': ['diagonal'], 'visual_driver': 'type', 'text_density': 'low'},
            'interpreted': {'tone': ['energetic'], 'transferable_concepts': [{'id':'order','reason':'repeat'}]},
            'techniques': ['flat_shapes'], 'typography': ['oversized'],
            'color': {'color_mode':'limited_palette','color_contrast':'strong','dominant_colors':['red']},
            'analysis': {'visual_mechanism':'circles repeat', 'transferable_method':'scale contrast'},
            'notes':'Not Swiss: swiss_international', 'rights_note':'Swiss photography research'}


ALIASES = {'瑞士国际主义':'swiss_international','swiss style':'swiss_international',
           '几何秩序':'geometric_order','拼贴':'collage_montage','对角动势':'diagonal',
           '字体主导':'type','图像主导':'image'}
CONTROLLED = {'swiss_international','geometric_order','collage_montage','diagonal','type','image','low','order','historical_affiliation','visual_affinity'}


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.a=case('P-0001',history=[{'term_id':'swiss_international','relation':'visual_affinity'},
                                    {'term_id':'new_typography','relation':'historical_affiliation'}])
        self.b=case('P-0002',family='collage_montage',creator='B')
        self.c=case('P-0003',creator='A')
        self.c['observed']['visual_driver']='image'
        self.items=[self.a,self.b,self.c]

    def run_query(self, query='', **kw):
        return search(self.items,query,ALIASES,CONTROLLED,**kw)

    def test_alias_phrases_cjk_and_dedup(self):
        self.assertEqual(normalize_query('Swiss Style 瑞士国际主义几何秩序',ALIASES),['swiss_international','geometric_order'])
        self.assertEqual(normalize_query('swiss stylesheet',ALIASES),['swiss','stylesheet'])

    def test_structured_only_and_all(self):
        self.assertEqual([r['id'] for r in self.run_query('瑞士国际主义')],['P-0001'])
        self.assertEqual([r['id'] for r in self.run_query('瑞士国际主义 图像主导',match='all')],[])
        self.assertEqual([r['id'] for r in self.run_query('瑞士国际主义 图像主导')],['P-0001','P-0003'])
        self.assertEqual(self.run_query('nonexistent'),[])

    def test_same_history_object(self):
        self.assertEqual(self.run_query(filters={'history':['swiss_international'],'relation':['historical_affiliation']}),[])
        self.assertEqual([r['id'] for r in self.run_query(filters={'history':['swiss_international'],'relation':['visual_affinity']})],['P-0001'])

    def test_facets_are_hard_constraints(self):
        rows=self.run_query(filters={'family':['collage_montage'],'composition':['diagonal'],'driver':['type']},diverse=True)
        self.assertEqual([r['id'] for r in rows],['P-0002'])
        self.assertIn('observed.visual_family',self.run_query('拼贴')[0]['matched_fields'])

    def test_diversity_and_relevance(self):
        rows=self.run_query(diverse=True)
        self.assertEqual({r['id'] for r in rows},{'P-0001','P-0002','P-0003'})
        self.assertEqual({r['creator'] for r in rows[:2]},{'A','B'})
        self.assertEqual(self.run_query(diverse=True),self.run_query(diverse=True))
        self.assertEqual(self.run_query('字体主导 几何秩序',diverse=True)[0]['id'],'P-0001')
        self.assertEqual(len(self.run_query(limit=0)),0)

    def test_partial_matches_explain_requested_and_missing_terms(self):
        rows=self.run_query('瑞士国际主义 图像主导 图像主导')
        self.assertEqual(rows[0].get('query_terms'),['swiss_international','image'])
        self.assertEqual(rows[0]['matched_terms'],['swiss_international'])
        self.assertEqual(rows[0]['missing_terms'],['image'])
        self.assertEqual(rows[1]['missing_terms'],['swiss_international'])
        self.assertEqual(self.run_query()[0]['query_terms'],[])
        self.assertEqual(self.run_query()[0]['missing_terms'],[])

    def test_diversity_covers_query_meanings_before_visual_variety_with_browser_parity(self):
        families=['geometric_order','collage_montage','symbolic_reduction','expressive_type']
        items=[case(f'P-{i+1:04d}',family=family,creator=chr(65+i)) for i,family in enumerate(families)]
        for cid,concept in [('P-0005','aggregation'),('P-0006','time')]:
            extra=case(cid)
            extra['interpreted']['transferable_concepts']=[{'id':concept,'reason':'specific meaning'}]
            items.append(extra)
        controlled=CONTROLLED | {'aggregation','time'}
        query='order aggregation time'
        rows=search(items,query,ALIASES,controlled,diverse=True,limit=4)
        self.assertEqual({term for r in rows[:3] for term in r['matched_terms']},{'order','aggregation','time'})
        self.assertGreaterEqual(len({r['family'] for r in rows}),2)
        ordinary=search(items,query,ALIASES,controlled,limit=4)
        self.assertEqual(len(ordinary),4)
        self.assertEqual({r['query_coverage'] for r in ordinary},{1})
        node=shutil.which('node')
        if not node: self.skipTest('Node runtime unavailable')
        script=browser_engine(ALIASES,controlled)+'\nprocess.stdout.write(JSON.stringify(PosterSearch.search('+json.dumps(items)+','+json.dumps(query)+',{"diverse":true,"limit":4})));'
        actual=json.loads(subprocess.check_output([str(node),'-e',script],text=True,encoding='utf-8'))
        self.assertEqual(actual,rows)

    def test_diversity_keeps_higher_coverage_group_before_uncovered_meaning(self):
        for item in (self.a,self.b):
            item['interpreted']['transferable_concepts'].append({'id':'aggregation','reason':'grouping'})
        self.c['interpreted']['transferable_concepts']=[{'id':'time','reason':'sequence'}]
        rows=search(self.items,'order aggregation time',ALIASES,CONTROLLED | {'aggregation','time'},diverse=True)
        self.assertEqual([r['query_coverage'] for r in rows],[2,2,1])
        self.assertEqual([r['id'] for r in rows],['P-0001','P-0002','P-0003'])

    def test_browser_engine_parity(self):
        node=shutil.which('node')
        if not node: self.skipTest('Node runtime unavailable')
        queries=[('',{}),('Swiss Style 瑞士国际主义几何秩序',{}),('瑞士国际主义 图像主导',{'match':'all'}),
                 ('字体主导',{'diverse':True}),('',{'filters':{'history':['swiss_international'],'relation':['historical_affiliation']}}),
                 ('',{'filters':{'family':['collage_montage']}}),('nonexistent',{})]
        for query,options in queries:
            expected=self.run_query(query,**options)
            script=browser_engine(ALIASES,CONTROLLED)+'\nprocess.stdout.write(JSON.stringify(PosterSearch.search('+json.dumps(self.items)+','+json.dumps(query)+','+json.dumps(options)+')));'
            actual=json.loads(subprocess.check_output([str(node),'-e',script],text=True,encoding='utf-8'))
            self.assertEqual(actual,expected,(query,options))


if __name__=='__main__':unittest.main()
