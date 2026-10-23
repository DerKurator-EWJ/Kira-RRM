"""Conservative, ID-invariant structural matching of small directed typed graphs.

No causal inference: edges supplied to the matcher must already be supported.
Predictions transferred between graphs are *unverified hypotheses*.
"""
import itertools
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MAX_NODES = 7


class RelationGraph:
    def __init__(self, nodes, edges):
        self.nodes = tuple(nodes)
        if not self.nodes or len(self.nodes) > MAX_NODES or len(set(self.nodes)) != len(self.nodes):
            raise ValueError('expected 1..7 distinct node IDs')
        self.edges = set()
        for src, relation, dst in edges:
            if src not in self.nodes or dst not in self.nodes:
                raise ValueError('edge endpoint missing from nodes')
            if not isinstance(relation, str) or not relation:
                raise ValueError('relation must be nonempty text')
            self.edges.add((src, relation, dst))

    def to_json(self):
        return json.dumps({'nodes': list(self.nodes), 'edges': [list(e) for e in sorted(self.edges, key=repr)]}, ensure_ascii=False)


def mappings(source, target, limit=2):
    """Enumerate up to `limit` bijections preserving direction and edge labels.

    Two maps mean correspondence is ambiguous, even if a match exists.
    This is exponential and deliberately limited to <=7 nodes.
    """
    if len(source.nodes) != len(target.nodes) or len(source.edges) != len(target.edges):
        return []
    # Signatures prune candidate permutations without relying on names/IDs.
    def signature(graph, node):
        incoming = sorted(label for a,label,b in graph.edges if b == node)
        outgoing = sorted(label for a,label,b in graph.edges if a == node)
        return (tuple(incoming), tuple(outgoing))
    source_nodes = sorted(source.nodes, key=lambda x: (signature(source,x), repr(x)))
    target_nodes = sorted(target.nodes, key=repr)
    candidates = {s: [t for t in target_nodes if signature(source,s)==signature(target,t)] for s in source_nodes}
    if any(not values for values in candidates.values()): return []
    source_nodes.sort(key=lambda s:(len(candidates[s]),repr(s)))
    found=[]
    def search(i, assignment, used):
        if len(found)>=limit:return
        if i==len(source_nodes):
            if {(assignment[a],label,assignment[b]) for a,label,b in source.edges}==target.edges:
                found.append(dict(assignment))
            return
        s=source_nodes[i]
        for t in candidates[s]:
            if t in used:continue
            assignment[s]=t
            # Check already assigned edges, including self loops.
            if all((assignment[a],label,assignment[b]) in target.edges for a,label,b in source.edges if a in assignment and b in assignment):
                search(i+1,assignment,used|{t})
            del assignment[s]
    search(0,{},set())
    return found


def transfer(source, target, proposals):
    """Transfer source proposals only if the structural map is unique.

    Proposals are (source_id, target_id, label) and must be source graph edges.
    Returned entries are hypotheses, never causal confirmations.
    """
    matches=mappings(source,target)
    if len(matches)!=1:
        return {'status':'NO_MATCH' if not matches else 'AMBIGUOUS', 'proposals':[]}
    mapping=matches[0]
    output=[]
    for a,b,label in proposals:
        if (a,label,b) not in source.edges:
            raise ValueError('proposal not supported by source graph')
        output.append({'source':mapping[a], 'target':mapping[b], 'relation':label, 'status':'UNVERIFIED_TRANSFER'})
    return {'status':'UNIQUE_MATCH','mapping':mapping,'proposals':output}


class GeneralizationStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.execute("""CREATE TABLE IF NOT EXISTS generalization_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT NOT NULL,
            source_graph TEXT NOT NULL, target_graph TEXT NOT NULL,
            status TEXT NOT NULL, result_json TEXT NOT NULL)""")
        self.db.commit()

    def record(self, source, target, result):
        with self.db:
            cursor=self.db.execute("""INSERT INTO generalization_runs
                (created_utc,source_graph,target_graph,status,result_json)
                VALUES(?,?,?,?,?)""",(
                    datetime.now(timezone.utc).isoformat(),source.to_json(),target.to_json(),
                    result['status'],json.dumps(result,ensure_ascii=False)))
        return cursor.lastrowid

    def history(self, limit=10):
        if not 1<=limit<=100:raise ValueError('limit must be 1..100')
        return [{'id':r[0],'status':r[1],'result':json.loads(r[2])}
                for r in self.db.execute('SELECT id,status,result_json FROM generalization_runs ORDER BY id DESC LIMIT ?',(limit,))]

    def close(self):self.db.close()
