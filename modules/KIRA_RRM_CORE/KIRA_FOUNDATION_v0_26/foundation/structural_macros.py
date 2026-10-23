"""ID-independent, evidence-qualified structural motif macros.

Motifs are connected edge subsets, with a bounded exhaustive canonicalization.
Labels and edge directions remain significant. This is not semantic understanding.
"""
import hashlib
import itertools
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def canonical_motif(edges):
    """Canonical graph signature independent of node IDs, up to 5 vertices."""
    edges = tuple(set(tuple(e) for e in edges))
    if not edges:
        raise ValueError('motif requires an edge')
    vertices = sorted({n for a, _, b in edges for n in (a,b)}, key=repr)
    if len(vertices) > 5:
        raise ValueError('motif exceeds five vertices')
    best = None
    for perm in itertools.permutations(range(len(vertices))):
        mapping = dict(zip(vertices,perm))
        candidate = (len(vertices),tuple(sorted((mapping[a],str(label),mapping[b]) for a,label,b in edges)))
        if best is None or candidate < best:
            best = candidate
    return json.dumps(best,separators=(',',':'),ensure_ascii=False)


def connected(edges):
    vertices = {v for a,_,b in edges for v in (a,b)}
    adjacency = defaultdict(set)
    for a,_,b in edges:
        adjacency[a].add(b);adjacency[b].add(a)
    seen=set(); todo=[next(iter(vertices))]
    while todo:
        x=todo.pop()
        if x in seen:continue
        seen.add(x);todo.extend(adjacency[x]-seen)
    return seen==vertices


def motifs(graph, max_edges=3):
    """Return unique motifs *within one graph* (no inflated overlapping counts)."""
    if not 1<=max_edges<=3:raise ValueError('max_edges must be 1..3')
    edges=sorted(graph.edges,key=repr)
    signatures=set()
    for n in range(1,min(max_edges,len(edges))+1):
        for subset in itertools.combinations(edges,n):
            if connected(subset) and len({v for a,_,b in subset for v in (a,b)})<=5:
                signatures.add(canonical_motif(subset))
    return signatures


class StructuralMacroLab:
    def __init__(self,path='data/structural_macros.sqlite'):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS motif_macros(
            macro_id TEXT PRIMARY KEY, signature TEXT NOT NULL UNIQUE,
            edge_count INTEGER NOT NULL, node_count INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS motif_evidence(
            stream TEXT NOT NULL, macro_id TEXT NOT NULL, evidence_type TEXT NOT NULL,
            PRIMARY KEY(stream,macro_id),
            FOREIGN KEY(macro_id) REFERENCES motif_macros(macro_id));
        """)
        self.db.execute('PRAGMA foreign_keys=ON')
    def learn(self,stream,graph,evidence_type='OBSERVATIONAL_TEMPORAL',max_edges=3):
        if not stream:raise ValueError('stream required')
        signatures=motifs(graph,max_edges)
        with self.db:
            for signature in signatures:
                macro_id=hashlib.blake2b(signature.encode('utf8'),digest_size=16,person=b'KIRAMOTIFv015').hexdigest()
                node_count,edge_list=json.loads(signature)
                self.db.execute('INSERT OR IGNORE INTO motif_macros VALUES(?,?,?,?)',
                                (macro_id,signature,len(edge_list),node_count))
                self.db.execute('INSERT OR IGNORE INTO motif_evidence VALUES(?,?,?)',
                                (stream,macro_id,evidence_type))
        return len(signatures)
    def shared(self,streams,min_streams=2,min_edges=2):
        streams=tuple(dict.fromkeys(streams))
        if len(streams)<min_streams or min_streams<2:raise ValueError('at least two streams required')
        marks=','.join('?' for _ in streams)
        rows=self.db.execute(f"""SELECT m.macro_id,m.signature,m.edge_count,m.node_count,
             COUNT(DISTINCT e.stream) AS coverage, GROUP_CONCAT(e.stream) AS sources
             FROM motif_macros m JOIN motif_evidence e ON m.macro_id=e.macro_id
             WHERE e.stream IN ({marks}) AND m.edge_count>=?
             GROUP BY m.macro_id HAVING COUNT(DISTINCT e.stream)>=?
             ORDER BY m.edge_count DESC, coverage DESC,m.macro_id""",(*streams,min_edges,min_streams)).fetchall()
        return [{'macro_id':r[0],'signature':r[1],'edges':r[2],'nodes':r[3],
                 'streams':r[4],'sources':sorted(r[5].split(',')),
                 'status':'OBSERVED_STRUCTURAL_ANALOGY_UNVERIFIED'} for r in rows]
    def close(self):self.db.close()
