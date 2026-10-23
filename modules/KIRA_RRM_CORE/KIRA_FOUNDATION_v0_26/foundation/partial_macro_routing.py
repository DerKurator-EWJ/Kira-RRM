"""v0.18 bounded partial template reuse with concrete, checked edge witnesses.

A cached template may cover a proper subset of a new graph. Unmatched edges
are constructed as fresh leaves; reconstruction is checked on every run.
No performance improvement is assumed: benchmark both paths on the same graph.
"""
import itertools
import json
import sqlite3
import time
from pathlib import Path
from .hierarchical_structures import canonical_edges,build_hierarchy,reconstruct
from .macro_routing import bucket,vertices
from .generalization import RelationGraph


def embeddings(source,target,limit=20000):
    source=canonical_edges(source);target=canonical_edges(target)
    sa=vertices(source);tb=vertices(target)
    if not source or len(sa)>len(tb) or len(sa)>5 or len(tb)>7:return []
    if len(source)>len(target):return []
    target_set=set(target);found=[]
    for i,perm in enumerate(itertools.permutations(tb,len(sa))):
        if i>=limit:break
        mapping=dict(zip(sa,perm))
        if all((mapping[a],t,mapping[b]) in target_set for a,t,b in source):
            found.append(mapping)
    return found


def remap_edges(edges,mapping):
    return canonical_edges((mapping[int(a)],t,mapping[int(b)]) for a,t,b in edges)


def partial_plan(graph,templates):
    edges=canonical_edges(graph.edges)
    if not 1<=len(edges)<=12 or len(vertices(edges))>7:raise ValueError('requires 1..12 edges, <=7 vertices')
    candidates=[]
    for tid,old_edges in templates:
        for mapping in embeddings(old_edges,edges):
            covered=remap_edges(old_edges,mapping)
            candidates.append((tid,covered,mapping))
    # Deterministic maximum-edge greedy set packing; no overlapping witnesses.
    candidates.sort(key=lambda x:(-len(x[1]),x[0],x[1]))
    used=set();chosen=[]
    for tid,covered,mapping in candidates:
        if not set(covered)&used:
            used.update(covered);chosen.append({'template_id':tid,'edges':[list(e) for e in covered],
                                                'mapping':{str(k):v for k,v in mapping.items()}})
    remaining=[list(e) for e in edges if e not in used]
    result={'reused':chosen,'fresh_edges':remaining,'original_edges':[list(e) for e in edges],
            'reused_edge_count':len(used),'fresh_edge_count':len(remaining),
            'candidate_embeddings':len(candidates)}
    verify_plan(result)
    return result


def verify_plan(plan):
    original=canonical_edges(plan['original_edges'])
    segments=[canonical_edges(x['edges']) for x in plan['reused']]
    segments.append(canonical_edges(plan['fresh_edges']))
    flattened=[e for segment in segments for e in segment]
    if len(flattened)!=len(set(flattened)) or canonical_edges(flattened)!=original:
        raise ValueError('partial plan does not reconstruct graph exactly')
    return original


class PartialMacroRouter:
    def __init__(self,path='data/partial_router.sqlite'):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.executescript("""CREATE TABLE IF NOT EXISTS partial_templates(
          id INTEGER PRIMARY KEY AUTOINCREMENT, edges_json TEXT NOT NULL, fingerprint TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS partial_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,
          stream TEXT NOT NULL, plan_json TEXT NOT NULL, reused_edges INTEGER NOT NULL);""")
    def templates(self):
        return [(r[0],json.loads(r[1])) for r in self.db.execute('SELECT id,edges_json FROM partial_templates ORDER BY id')]
    def register(self,graph):
        edges=canonical_edges(graph.edges)
        if not edges or len(edges)>12 or len(vertices(edges))>5:raise ValueError('template exceeds bounds')
        # Deduplicate isomorphic templates to keep the index bounded.
        from .macro_routing import mapping_for
        for tid,old in self.templates():
            if mapping_for(old,edges) is not None:return tid
        with self.db:
            return self.db.execute('INSERT INTO partial_templates(edges_json,fingerprint) VALUES(?,?)',
                                   (json.dumps(edges),bucket(edges))).lastrowid
    def learn(self,stream,graph,register_new=True):
        if not stream:raise ValueError('stream required')
        plan=partial_plan(graph,self.templates())
        with self.db:
            run=self.db.execute('INSERT INTO partial_runs(stream,plan_json,reused_edges) VALUES(?,?,?)',
                                (stream,json.dumps(plan,sort_keys=True),plan['reused_edge_count'])).lastrowid
        # Store whole graph for future reuse only if it meets template vertex bound.
        if register_new and len(vertices(canonical_edges(graph.edges)))<=5:self.register(graph)
        return run,plan
    def load(self,run_id):
        row=self.db.execute('SELECT plan_json FROM partial_runs WHERE id=?',(run_id,)).fetchone()
        if row is None:raise KeyError(run_id)
        plan=json.loads(row[0]);verify_plan(plan);return plan
    def close(self):self.db.close()


def benchmark(graph,templates,repeats=30):
    if not 1<=repeats<=1000:raise ValueError('invalid repeats')
    # Wall-clock comparison of entire baseline hierarchy construction vs planning.
    # The outputs differ: a plan is not a fully constructed hierarchy.
    a=time.perf_counter()
    for _ in range(repeats):reconstruct(build_hierarchy(graph))
    baseline=(time.perf_counter()-a)/repeats
    b=time.perf_counter()
    for _ in range(repeats):partial_plan(graph,templates)
    routed=(time.perf_counter()-b)/repeats
    return {'baseline_hierarchy_ms':round(baseline*1000,5),
            'partial_plan_ms':round(routed*1000,5),'repeats':repeats,
            'note':'Different output workloads; not a speedup proof.'}
