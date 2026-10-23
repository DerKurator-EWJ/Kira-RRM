"""Bounded, lossless hierarchy of graph motifs with explicit concrete witnesses.

A hierarchy is a structural representation, not a compressed file or a causal claim.
Each level combines connected, edge-disjoint components; all graph edges survive.
"""
import hashlib
import itertools
import json
import sqlite3
from pathlib import Path
from .structural_macros import canonical_motif, connected


def signature_id(signature):
    return hashlib.blake2b(signature.encode('utf8'),digest_size=16,person=b'KIRAHIERv016').hexdigest()


def canonical_edges(edges):
    return tuple(sorted({(int(a),str(t),int(b)) for a,t,b in edges}))


def connected_components(edges):
    """Partition edges into connected components (edge-disjoint, deterministic)."""
    remaining=set(edges)
    result=[]
    while remaining:
        seed=min(remaining); component={seed};remaining.remove(seed)
        nodes={seed[0],seed[2]}
        changed=True
        while changed:
            changed=False
            for e in sorted(remaining):
                if e[0] in nodes or e[2] in nodes:
                    component.add(e);nodes.update((e[0],e[2]));remaining.remove(e);changed=True
        result.append(tuple(sorted(component)))
    return result


def build_hierarchy(graph,max_edges=12):
    """Create deterministic 1-edge leaves and recursively merge touching components.

    Only graphs with <= max_edges and <=5 vertices per merged motif are supported.
    All edges are retained exactly, and each parent references its two children.
    """
    edges=canonical_edges(graph.edges)
    if not edges or len(edges)>max_edges:raise ValueError('graph must contain 1..%d unique edges'%max_edges)
    active=[]; nodes={}; level=0
    for e in edges:
        sig=canonical_motif((e,));mid=signature_id(sig)
        key='leaf:'+str(len(nodes))
        nodes[key]={'key':key,'macro_id':mid,'signature':sig,'edges':[list(e)],'children':[],'level':0}
        active.append(key)
    while len(active)>1:
        chosen=None
        for i,j in itertools.combinations(range(len(active)),2):
            a,b=nodes[active[i]],nodes[active[j]]
            aa=canonical_edges(a['edges']);bb=canonical_edges(b['edges'])
            vertices={v for x,_,y in aa+bb for v in (x,y)}
            if len(vertices)<=5 and connected(aa+bb):
                chosen=(i,j);break
        if chosen is None:break
        i,j=chosen;ka,kb=active[i],active[j]
        merged=canonical_edges(nodes[ka]['edges']+nodes[kb]['edges'])
        sig=canonical_motif(merged)
        level+=1;key='parent:'+str(level)
        nodes[key]={'key':key,'macro_id':signature_id(sig),'signature':sig,
                    'edges':[list(e) for e in merged],'children':[ka,kb],
                    'level':1+max(nodes[ka]['level'],nodes[kb]['level'])}
        active=[k for n,k in enumerate(active) if n not in (i,j)]+[key]
    return {'nodes':nodes,'roots':active,'original_edges':[list(e) for e in edges]}


def reconstruct(tree):
    nodes=tree['nodes'];visited=set()
    def walk(key):
        if key in visited:raise ValueError('cycle or duplicate child reference')
        visited.add(key)
        node=nodes[key]
        if not node['children']:return canonical_edges(node['edges'])
        if len(node['children'])!=2:raise ValueError('binary parent required')
        children=canonical_edges(walk(node['children'][0])+walk(node['children'][1]))
        if children!=canonical_edges(node['edges']):raise ValueError('parent witness mismatch')
        if canonical_motif(children)!=node['signature']:raise ValueError('signature mismatch')
        return children
    edges=canonical_edges(e for key in tree['roots'] for e in walk(key))
    if visited!=set(nodes):raise ValueError('unreachable nodes')
    if edges!=canonical_edges(tree['original_edges']):raise ValueError('roundtrip mismatch')
    return edges


class HierarchyLab:
    def __init__(self,path='data/hierarchies.sqlite'):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""CREATE TABLE IF NOT EXISTS hierarchy_runs(
            run_id INTEGER PRIMARY KEY AUTOINCREMENT, stream TEXT NOT NULL,
            tree_json TEXT NOT NULL, created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS hierarchy_macros(
            macro_id TEXT PRIMARY KEY,signature TEXT NOT NULL UNIQUE,
            occurrences INTEGER NOT NULL DEFAULT 0);""")
    def learn(self,stream,graph):
        if not stream:raise ValueError('stream required')
        tree=build_hierarchy(graph)
        reconstruct(tree)
        with self.db:
            cursor=self.db.execute('INSERT INTO hierarchy_runs(stream,tree_json) VALUES(?,?)',
                                   (stream,json.dumps(tree,sort_keys=True)))
            # Count at most one occurrence per macro per graph, not repeated internal witnesses.
            unique={(n['macro_id'],n['signature']) for n in tree['nodes'].values()}
            for mid,sig in unique:
                self.db.execute('INSERT INTO hierarchy_macros(macro_id,signature,occurrences) VALUES(?,?,1) '
                                'ON CONFLICT(macro_id) DO UPDATE SET occurrences=occurrences+1',(mid,sig))
        return cursor.lastrowid,tree
    def load(self,run_id):
        row=self.db.execute('SELECT tree_json FROM hierarchy_runs WHERE run_id=?',(run_id,)).fetchone()
        if row is None:raise KeyError(run_id)
        tree=json.loads(row[0]);reconstruct(tree);return tree
    def shared(self,min_occurrences=2):
        return self.db.execute('SELECT macro_id,occurrences FROM hierarchy_macros '
                               'WHERE occurrences>=? ORDER BY occurrences DESC,macro_id',(min_occurrences,)).fetchall()
    def close(self):self.db.close()
