"""RRM 0.2: finite relational states, structural transition evidence, open inquiries.
Experimental semantics, not a complete formalization of RRM or general AI.
"""
import json
import sqlite3
from collections import Counter


def canonical(state):
    """Canonicalize a finite directed labeled multigraph up to renaming node IDs.
    Exact brute force for <=7 nodes; fail explicitly above that bound.
    Node labels and edge labels are preserved; edges are directed.
    """
    from itertools import permutations
    nodes = state['nodes']
    edges = state['edges']
    if len(nodes) > 7:
        raise ValueError('Exact canonicalization supports at most 7 nodes; no silent approximation')
    if len(set(nodes)) != len(nodes):
        raise ValueError('Duplicate node ID')
    if any(a not in nodes or b not in nodes for a, _, b in edges):
        raise ValueError('Edge refers to absent node')
    # Group by node label to reduce permutations, preserving labels.
    labels = sorted(set(nodes.values()))
    groups = [[n for n in nodes if nodes[n] == label] for label in labels]
    from itertools import product
    orders = []
    for combination in product(*(permutations(group) for group in groups)):
        order = [n for group in combination for n in group]
        idx = {node: i for i, node in enumerate(order)}
        representation = (tuple(nodes[n] for n in order), tuple(sorted((idx[a], rel, idx[b]) for a, rel, b in edges)))
        orders.append(representation)
    return json.dumps(min(orders), ensure_ascii=False, separators=(',', ':'))


class RelationalCore:
    def __init__(self, path='rrm.sqlite'):
        self.db = sqlite3.connect(path)
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS observations (stream TEXT, pos INTEGER, signature TEXT NOT NULL, raw TEXT NOT NULL, PRIMARY KEY(stream,pos))')
            self.db.execute('CREATE TABLE IF NOT EXISTS evidence (stream TEXT, source TEXT, target TEXT, count INTEGER NOT NULL, PRIMARY KEY(stream,source,target))')
            self.db.execute('CREATE TABLE IF NOT EXISTS inquiries (stream TEXT, signature TEXT, question TEXT, status TEXT, PRIMARY KEY(stream,signature,question))')

    def observe(self, stream, state):
        signature = canonical(state)
        row = self.db.execute('SELECT pos,signature FROM observations WHERE stream=? ORDER BY pos DESC LIMIT 1', (stream,)).fetchone()
        pos = 0 if row is None else row[0] + 1
        prior_prediction = self.predict(stream,signature=row[1]) if row else {'state':'OPEN'}
        with self.db:
            if row is not None:
                self.db.execute('INSERT INTO evidence VALUES (?,?,?,1) ON CONFLICT(stream,source,target) DO UPDATE SET count=count+1', (stream,row[1],signature))
            self.db.execute('INSERT INTO observations VALUES (?,?,?,?)', (stream,pos,signature,json.dumps(state,ensure_ascii=False)))
        return {'position':pos,'signature':signature,'prediction_before':prior_prediction}

    def predict(self, stream, state=None, signature=None):
        if signature is None:
            if state is not None:
                signature = canonical(state)
            else:
                row = self.db.execute('SELECT signature FROM observations WHERE stream=? ORDER BY pos DESC LIMIT 1',(stream,)).fetchone()
                if row is None:
                    return {'state':'OPEN','reason':'no observation'}
                signature = row[0]
        choices = self.db.execute('SELECT target,count FROM evidence WHERE stream=? AND source=? ORDER BY count DESC,target', (stream,signature)).fetchall()
        if not choices:
            return {'state':'OPEN','reason':'no observed continuation','source':signature}
        total = sum(count for _,count in choices)
        return {'state':'HYPOTHESIS','next_signature':choices[0][0], 'support':total, 'frequency':choices[0][1]/total,'alternatives':choices}

    def dream(self, stream, steps=5):
        row = self.db.execute('SELECT signature FROM observations WHERE stream=? ORDER BY pos DESC LIMIT 1',(stream,)).fetchone()
        if row is None:
            return {'status':'HYPOTHETICAL','signatures':[],'reason':'no observation'}
        signature = row[0]
        generated=[]
        for _ in range(max(0,steps)):
            prediction = self.predict(stream,signature=signature)
            if prediction['state']=='OPEN':
                break
            signature=prediction['next_signature']
            generated.append(signature)
        return {'status':'HYPOTHETICAL','signatures':generated,'stopped_early':len(generated)<steps}

    def ask(self, stream, state, question):
        signature = canonical(state)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO inquiries VALUES (?,?,?,?)',(stream,signature,question,'OPEN'))
        return {'state':'OPEN','question':question,'signature':signature}

    def questions(self, stream):
        return self.db.execute('SELECT question,status FROM inquiries WHERE stream=? ORDER BY question',(stream,)).fetchall()

    def count(self, stream):
        return self.db.execute('SELECT COUNT(*) FROM observations WHERE stream=?',(stream,)).fetchone()[0]
