"""RRM 0.4: context-conditioned, evidence-counted relation hypotheses.

A conservative experiment, not causal reasoning or a universal learner.
The local context is a multiset of typed edges incident to the changed pair.
"""
import json
from collections import Counter
from rrm03 import RuleCore


def local_context(state, a, b, excluded_index):
    """Invariant to node IDs; describes other edges attached to endpoints a,b."""
    tokens=[]
    for i,(x,rel,y) in enumerate(state['edges']):
        if i==excluded_index: continue
        if x not in (a,b) and y not in (a,b): continue
        def role(n):
            if n==a: return 'SRC'
            if n==b: return 'DST'
            return 'OTHER:'+state['nodes'][n]
        tokens.append((role(x),rel,role(y)))
    return json.dumps(sorted(tokens),ensure_ascii=False,separators=(',',':'))


def examples(previous, current):
    """Extract unambiguous candidate edge outcomes with stable node IDs.
    No node births/deaths or multiple changes. Identical state => NO_CHANGE evidence.
    """
    if previous['nodes'] != current['nodes'] or len(previous['edges']) != len(current['edges']):
        return []
    old=previous['edges']; new=current['edges']
    changed=[i for i,(x,y) in enumerate(zip(old,new)) if x!=y]
    if len(changed)>1: return []
    if len(changed)==1:
        i=changed[0]
        a,r,b=old[i]; x,newrel,y=new[i]
        if (a,b)!=(x,y) or r==newrel: return []
        return [(previous['nodes'][a],r,previous['nodes'][b],local_context(previous,a,b,i),newrel)]
    # Explicit non-change is evidence for every unique eligible edge.
    result=[]
    for i,(a,r,b) in enumerate(old):
        key=(previous['nodes'][a],r,previous['nodes'][b],local_context(previous,a,b,i),'NO_CHANGE')
        if key not in result: result.append(key)
    return result


class ContextCore(RuleCore):
    def __init__(self,path='rrm.sqlite'):
        super().__init__(path)
        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS contextual_evidence
                (stream TEXT, src_type TEXT, old_rel TEXT, dst_type TEXT,
                 context TEXT, outcome TEXT, support INTEGER NOT NULL,
                 PRIMARY KEY(stream,src_type,old_rel,dst_type,context,outcome))''')

    def observe(self,stream,state):
        previous=self._last.get(stream)
        if previous is None:
            row=self.db.execute('SELECT raw FROM observations WHERE stream=? ORDER BY pos DESC LIMIT 1',(stream,)).fetchone()
            if row: previous=json.loads(row[0])
        result=super().observe(stream,state)
        if previous is not None:
            with self.db:
                for st,old,dt,ctx,outcome in examples(previous,state):
                    self.db.execute('''INSERT INTO contextual_evidence VALUES (?,?,?,?,?,?,1)
                        ON CONFLICT(stream,src_type,old_rel,dst_type,context,outcome)
                        DO UPDATE SET support=support+1''',(stream,st,old,dt,ctx,outcome))
        return result

    def explain(self,stream,state,min_support=2,focus=None):
        """Return a unique sufficiently supported conditional outcome or OPEN.
        No defaulting to an unconditional rule on unseen contexts.
        """
        candidates=[]
        for i,(a,rel,b) in enumerate(state['edges']):
            if focus is not None and i != focus: continue
            st,dt=state['nodes'][a],state['nodes'][b]
            ctx=local_context(state,a,b,i)
            rows=self.db.execute('''SELECT outcome,support FROM contextual_evidence
                 WHERE stream=? AND src_type=? AND old_rel=? AND dst_type=? AND context=?
                 ORDER BY support DESC,outcome''',(stream,st,rel,dt,ctx)).fetchall()
            if not rows: continue
            total=sum(n for _,n in rows)
            if total<min_support: continue
            best=rows[0][1]
            if len(rows)>1 and rows[1][1]==best:
                return {'state':'OPEN','reason':'equally supported outcomes','context':json.loads(ctx),'alternatives':rows}
            candidates.append((i,rows[0][0],best,total,ctx,rows))
        if not candidates:
            return {'state':'OPEN','reason':'unseen or insufficiently supported context', 'question':'Welche Bedingungen bestimmen den nächsten Zustand?'}
        if len(candidates)!=1:
            return {'state':'OPEN','reason':'multiple applicable edges; no unique target'}
        i,outcome,best,total,ctx,rows=candidates[0]
        result=json.loads(json.dumps(state))
        if outcome!='NO_CHANGE': result['edges'][i][1]=outcome
        return {'state':'HYPOTHESIS','result':result,'outcome':outcome,
                'support':best,'observations':total,'frequency':best/total,
                'context':json.loads(ctx),'alternatives':rows,
                'question':('Welche Bedingung unterscheidet die beobachteten Ausgänge?' if len(rows)>1 else None)}
