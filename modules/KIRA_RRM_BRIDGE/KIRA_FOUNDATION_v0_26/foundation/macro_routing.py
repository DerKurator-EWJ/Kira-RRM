"""Bounded structural-template routing, with verified concrete witnesses.

Index narrows candidates by ID-independent degree/label features. Candidate
isomorphism is checked exactly; otherwise hierarchy is rebuilt. Templates
are stored in SQLite and reused across restarts. This is a research baseline.
"""
import itertools
import json
import sqlite3
from collections import Counter
from pathlib import Path
from .hierarchical_structures import build_hierarchy, canonical_edges, reconstruct


def vertices(edges):
    return sorted({v for a,_,b in edges for v in (a,b)})


def bucket(edges):
    edges=canonical_edges(edges)
    degree=Counter()
    for a,t,b in edges:
        degree[(a,'out',t)]+=1
        degree[(b,'in',t)]+=1
    v=vertices(edges)
    features=[]
    for node in v:
        features.append(tuple(sorted((direction,label,count) for (n,direction,label),count in degree.items() if n==node)))
    return json.dumps([len(v),len(edges),sorted(features)],separators=(',',':'))


def mapping_for(source,target):
    """Return exact source->target vertex mapping, or None. Up to 5 vertices."""
    source=canonical_edges(source);target=canonical_edges(target)
    a=vertices(source);b=vertices(target)
    if len(a)!=len(b) or len(a)>5 or bucket(source)!=bucket(target):return None
    target_set=set(target)
    for perm in itertools.permutations(b):
        mapping=dict(zip(a,perm))
        if {(mapping[x],t,mapping[y]) for x,t,y in source}==target_set:
            return mapping
    return None


def remap_tree(tree,mapping):
    def remap(edges):
        return [[mapping[int(a)],t,mapping[int(b)]] for a,t,b in edges]
    result={'nodes':{},'roots':list(tree['roots']), 'original_edges':remap(tree['original_edges'])}
    for key,node in tree['nodes'].items():
        n=dict(node)
        n['edges']=remap(node['edges'])
        result['nodes'][key]=n
    reconstruct(result)
    return result


class MacroRouter:
    def __init__(self,path='data/macro_router.sqlite'):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""CREATE TABLE IF NOT EXISTS routing_templates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bucket TEXT NOT NULL, edges_json TEXT NOT NULL,
            tree_json TEXT NOT NULL, hits INTEGER NOT NULL DEFAULT 0);
            CREATE INDEX IF NOT EXISTS routing_bucket_idx ON routing_templates(bucket);
            CREATE TABLE IF NOT EXISTS routing_runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, stream TEXT NOT NULL,
            template_id INTEGER NOT NULL, cache_hit INTEGER NOT NULL,
            tree_json TEXT NOT NULL,
            FOREIGN KEY(template_id) REFERENCES routing_templates(id));""")

    def learn(self,stream,graph):
        if not stream:raise ValueError('stream required')
        edges=canonical_edges(graph.edges)
        if not edges or len(edges)>12:raise ValueError('requires 1..12 edges')
        b=bucket(edges)
        candidates=self.db.execute('SELECT id,edges_json,tree_json FROM routing_templates WHERE bucket=? ORDER BY id',(b,)).fetchall()
        template_id=None;hit=False;tree=None
        for candidate_id,edge_json,tree_json in candidates:
            old_edges=json.loads(edge_json)
            match=mapping_for(old_edges,edges)
            if match is not None:
                candidate=remap_tree(json.loads(tree_json),match)
                if canonical_edges(candidate['original_edges'])!=edges:raise AssertionError('bad template')
                template_id=candidate_id;tree=candidate;hit=True
                break
        if tree is None:
            tree=build_hierarchy(graph)
            reconstruct(tree)
        with self.db:
            if template_id is None:
                cursor=self.db.execute('INSERT INTO routing_templates(bucket,edges_json,tree_json) VALUES(?,?,?)',
                    (b,json.dumps(edges),json.dumps(tree,sort_keys=True)))
                template_id=cursor.lastrowid
            else:
                self.db.execute('UPDATE routing_templates SET hits=hits+1 WHERE id=?',(template_id,))
            run=self.db.execute('INSERT INTO routing_runs(stream,template_id,cache_hit,tree_json) VALUES(?,?,?,?)',
                (stream,template_id,int(hit),json.dumps(tree,sort_keys=True))).lastrowid
        return {'run_id':run,'template_id':template_id,'cache_hit':hit,
                'candidate_count':len(candidates),'tree':tree}

    def stats(self):
        templates=self.db.execute('SELECT COUNT(*),COALESCE(SUM(hits),0) FROM routing_templates').fetchone()
        runs=self.db.execute('SELECT COUNT(*),COALESCE(SUM(cache_hit),0) FROM routing_runs').fetchone()
        return {'templates':templates[0],'template_hits':templates[1], 'runs':runs[0],'cache_hits':runs[1]}

    def load(self,run_id):
        row=self.db.execute('SELECT tree_json FROM routing_runs WHERE id=?',(run_id,)).fetchone()
        if row is None:raise KeyError(run_id)
        tree=json.loads(row[0]);reconstruct(tree);return tree

    def close(self):self.db.close()
