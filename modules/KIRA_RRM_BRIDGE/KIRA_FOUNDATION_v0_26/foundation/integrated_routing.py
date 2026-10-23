"""v0.19: partial template matches become actual hierarchy leaves, with witnesses.

This is a hierarchical cover, not a byte-compression claim. Both baseline and
routed paths produce losslessly reconstructable graph hierarchies, not identical
node layouts. Matching is bounded exhaustive search, so speedup is not assumed.
"""
import json
import sqlite3
import time
from pathlib import Path
from .generalization import RelationGraph
from .hierarchical_structures import (build_hierarchy, canonical_edges, reconstruct,
                                      signature_id, connected)
from .structural_macros import canonical_motif
from .partial_macro_routing import partial_plan, verify_plan
from .macro_routing import vertices


def build_integrated(graph, templates):
    edges=canonical_edges(graph.edges)
    plan=partial_plan(graph,templates)
    nodes={};roots=[]; reused=0
    # A template becomes one verified macro leaf rather than being expanded and rebuilt.
    for item in plan['reused']:
        subset=canonical_edges(item['edges'])
        if not subset:raise ValueError('empty reused template')
        key='reuse:'+str(len(roots))
        sig=canonical_motif(subset)
        nodes[key]={'key':key,'macro_id':signature_id(sig),'signature':sig,
                    'edges':[list(e) for e in subset], 'children':[], 'level':0,
                    'template_id':item['template_id'],'reused':True}
        roots.append(key);reused+=len(subset)
    for edge in canonical_edges(plan['fresh_edges']):
        key='fresh:'+str(len(roots));sig=canonical_motif((edge,))
        nodes[key]={'key':key,'macro_id':signature_id(sig),'signature':sig,
                    'edges':[list(edge)],'children':[],'level':0,'reused':False}
        roots.append(key)
    merges=0
    while len(roots)>1:
        pair=None
        for i in range(len(roots)):
            for j in range(i+1,len(roots)):
                aa=canonical_edges(nodes[roots[i]]['edges']);bb=canonical_edges(nodes[roots[j]]['edges'])
                union=canonical_edges(aa+bb)
                if len(vertices(union))<=5 and connected(union):
                    pair=(i,j,union);break
            if pair:break
        if pair is None:break
        i,j,union=pair;left,right=roots[i],roots[j]
        key='merge:'+str(merges);sig=canonical_motif(union)
        nodes[key]={'key':key,'macro_id':signature_id(sig),'signature':sig,
                    'edges':[list(e) for e in union], 'children':[left,right],
                    'level':1+max(nodes[left]['level'],nodes[right]['level'])}
        roots=[r for n,r in enumerate(roots) if n not in (i,j)]+[key]
        merges+=1
    tree={'nodes':nodes,'roots':roots,'original_edges':[list(e) for e in edges]}
    # The standard reconstruct() permits multi-edge leaves. Validate their signatures too.
    for node in nodes.values():
        if canonical_motif(canonical_edges(node['edges']))!=node['signature']:
            raise ValueError('invalid macro signature')
    if reconstruct(tree)!=verify_plan(plan):raise ValueError('graph mismatch')
    return {'tree':tree,'plan':plan,'reused_edges':reused,
            'fresh_edges':len(plan['fresh_edges']),'new_merges':merges}


class IntegratedRouter:
    def __init__(self,path='data/integrated.sqlite'):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.executescript("""CREATE TABLE IF NOT EXISTS templates(
          id INTEGER PRIMARY KEY, edges TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS runs(
          id INTEGER PRIMARY KEY, stream TEXT NOT NULL, result TEXT NOT NULL);""")
    def templates(self):
        return [(r[0],json.loads(r[1])) for r in self.db.execute('SELECT id,edges FROM templates ORDER BY id')]
    def register(self,graph):
        edges=canonical_edges(graph.edges)
        if not edges or len(edges)>12 or len(vertices(edges))>5:raise ValueError('template out of bounds')
        from .macro_routing import mapping_for
        for tid,old in self.templates():
            if mapping_for(old,edges) is not None:return tid
        with self.db:
            return self.db.execute('INSERT INTO templates(edges) VALUES(?)',(json.dumps(edges),)).lastrowid
    def learn(self,stream,graph,register_new=True):
        if not stream:raise ValueError('stream required')
        result=build_integrated(graph,self.templates())
        with self.db:
            run_id=self.db.execute('INSERT INTO runs(stream,result) VALUES(?,?)',
                         (stream,json.dumps(result,sort_keys=True))).lastrowid
        if register_new and len(vertices(canonical_edges(graph.edges)))<=5:self.register(graph)
        return run_id,result
    def load(self,run_id):
        row=self.db.execute('SELECT result FROM runs WHERE id=?',(run_id,)).fetchone()
        if row is None:raise KeyError(run_id)
        result=json.loads(row[0]);reconstruct(result['tree']);verify_plan(result['plan'])
        if canonical_edges(result['tree']['original_edges'])!=canonical_edges(result['plan']['original_edges']):
            raise ValueError('witness mismatch')
        return result
    def close(self):self.db.close()


def benchmark_equal_workload(graph,templates,repeats=50):
    if not 1<=repeats<=1000:raise ValueError('invalid repeats')
    base=[];routed=[];edges=canonical_edges(graph.edges)
    # Alternating order mitigates but does not eliminate runtime noise.
    for i in range(repeats):
        if i%2==0:order=('baseline','routed')
        else:order=('routed','baseline')
        for name in order:
            start=time.perf_counter_ns()
            if name=='baseline':
                tree=build_hierarchy(graph);output=reconstruct(tree)
            else:
                result=build_integrated(graph,templates);output=reconstruct(result['tree'])
            elapsed=time.perf_counter_ns()-start
            if output!=edges:raise AssertionError('non-equivalent reconstruction')
            (base if name=='baseline' else routed).append(elapsed/1e6)
    return {'baseline_ms':round(sum(base)/len(base),6),
            'integrated_ms':round(sum(routed)/len(routed),6),
            'baseline_new_merges':sum(1 for n in build_hierarchy(graph)['nodes'].values() if n['children']),
            'integrated_new_merges':build_integrated(graph,templates)['new_merges'],
            'repeats':repeats,
            'note':'Same complete graph-reconstruction task; hierarchy topology may differ. Small Python microbenchmark, not a general speedup claim.'}
