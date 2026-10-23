"""Evidence-qualified relation graphs discovered from persistent event streams.
Temporal edges are NOT causal edges. Counts use consecutive ordered observations.
"""
import json
import sqlite3
from collections import Counter
from pathlib import Path
from .generalization import RelationGraph
from .partial_generalization import partial_matches

class EventGraphLab:
    def __init__(self, path='data/event_graph.sqlite'):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS graph_events(stream TEXT NOT NULL, seq INTEGER NOT NULL, token INTEGER NOT NULL, PRIMARY KEY(stream,seq));
        CREATE TABLE IF NOT EXISTS graph_snapshots(id INTEGER PRIMARY KEY AUTOINCREMENT, stream TEXT NOT NULL, evidence_json TEXT NOT NULL, created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
    def ingest(self,stream,tokens):
        if not stream: raise ValueError('stream required')
        tokens=list(tokens)
        if any(not isinstance(t,int) or isinstance(t,bool) for t in tokens): raise ValueError('integer IDs required')
        with self.db:
            row=self.db.execute('SELECT COALESCE(MAX(seq),0) FROM graph_events WHERE stream=?',(stream,)).fetchone()
            offset=row[0]
            self.db.executemany('INSERT INTO graph_events(stream,seq,token) VALUES(?,?,?)',[(stream,offset+i+1,t) for i,t in enumerate(tokens)])
        return len(tokens)
    def import_live(self,live_db,stream='audio:live',destination=None):
        """Import only previously unseen ticks, idempotently, from v0.7+ live.sqlite."""
        destination=destination or stream
        if not Path(live_db).exists():raise FileNotFoundError(live_db)
        conn=sqlite3.connect(str(live_db))
        try: rows=conn.execute('SELECT tick,token FROM live_events WHERE stream=? ORDER BY tick',(stream,)).fetchall()
        finally:conn.close()
        # Imported ticks are keyed by their original ticks in a dedicated stream.
        imported=0
        with self.db:
            for tick,token in rows:
                cur=self.db.execute('INSERT OR IGNORE INTO graph_events(stream,seq,token) VALUES(?,?,?)',(destination,tick,token))
                imported+=cur.rowcount
        return imported
    def evidence(self,stream,min_count=2,max_nodes=7):
        if min_count<1 or not 1<=max_nodes<=7:raise ValueError('invalid thresholds')
        tokens=[r[0] for r in self.db.execute('SELECT token FROM graph_events WHERE stream=? ORDER BY seq',(stream,))]
        # Distinguish temporal succession from symmetric adjacency; no interventions.
        freq=Counter(tokens)
        selected=sorted(freq,key=lambda t:(-freq[t],t))[:max_nodes]
        chosen=set(selected)
        directed=Counter((a,b) for a,b in zip(tokens,tokens[1:]) if a in chosen and b in chosen)
        edges=[]
        for (a,b),count in sorted(directed.items()):
            if count>=min_count: edges.append({'source':a,'target':b,'type':'PRECEDES','count':count,'evidence':'OBSERVATIONAL_TEMPORAL','causal':False})
        return {'stream':stream,'events':len(tokens),'nodes':selected,'edges':edges,'excluded_distinct_ids':max(0,len(freq)-len(selected))}
    def graph(self,stream,min_count=2,max_nodes=7):
        evidence=self.evidence(stream,min_count,max_nodes)
        if not evidence['nodes']:return None
        return RelationGraph(evidence['nodes'],[(e['source'],e['type'],e['target']) for e in evidence['edges']])
    def snapshot(self,stream,min_count=2,max_nodes=7):
        result=self.evidence(stream,min_count,max_nodes)
        with self.db:
            self.db.execute('INSERT INTO graph_snapshots(stream,evidence_json) VALUES(?,?)',(stream,json.dumps(result,sort_keys=True)))
        return result
    def compare(self,a,b,min_edges=1,min_precision=0.5):
        ga=self.graph(a);gb=self.graph(b)
        if ga is None or gb is None:return {'status':'INSUFFICIENT_DATA','matches':[]}
        return partial_matches(ga,gb,min_edges=min_edges,min_precision=min_precision)
    def close(self):self.db.close()
