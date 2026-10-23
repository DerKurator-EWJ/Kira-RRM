"""Empirical hypotheses about intervention effects; no causal certainty implied."""
import math
from datetime import datetime, timezone

class HypothesisEngine:
    """Evidence-driven, pre-registered candidates H_A/H_B, not free-form invention."""
    def __init__(self, lab, minimum_per_arm=30, effect_threshold=0.10, z=1.96):
        self.lab=lab
        self.minimum_per_arm=int(minimum_per_arm)
        self.effect_threshold=float(effect_threshold)
        self.z=float(z)
        if self.minimum_per_arm<1 or self.effect_threshold<0 or self.z<=0:raise ValueError('invalid settings')
        self.lab.db.execute("""CREATE TABLE IF NOT EXISTS hypothesis_reviews(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT NOT NULL,
            variable TEXT NOT NULL, hypothesis TEXT NOT NULL, status TEXT NOT NULL,
            n0 INTEGER NOT NULL,n1 INTEGER NOT NULL,effect REAL,ci_low REAL,ci_high REAL,
            event_count INTEGER NOT NULL)""")
        self.lab.db.commit()
    @staticmethod
    def _wilson(p,n,z):
        if not n:return (0.,1.)
        d=1+z*z/n
        center=(p+z*z/(2*n))/d
        half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
        return max(0.,center-half),min(1.,center+half)
    def evaluate(self,variable):
        if variable not in ('A','B'):raise ValueError('variable must be A or B')
        arms=[]
        for value in (0,1):
            n,s=self.lab.db.execute("""SELECT COUNT(*),COALESCE(SUM(y),0) FROM experiment_events
                WHERE kind='do' AND target=? AND value=?""",(variable,value)).fetchone()
            arms.append((n,s))
        (n0,s0),(n1,s1)=arms
        effect=low=high=None
        if min(n0,n1)<self.minimum_per_arm:status='OPEN_INSUFFICIENT_EVIDENCE'
        else:
            p0,p1=s0/n0,s1/n1
            effect=p1-p0
            # Conservative difference interval via separate Wilson score intervals.
            l0,u0=self._wilson(p0,n0,self.z);l1,u1=self._wilson(p1,n1,self.z)
            low,high=l1-u0,u1-l0
            if low>self.effect_threshold:status='SUPPORTED_POSITIVE_EFFECT'
            elif high < -self.effect_threshold:status='SUPPORTED_NEGATIVE_EFFECT'
            elif low>=-self.effect_threshold and high<=self.effect_threshold:status='SUPPORTED_NEGLIGIBLE_EFFECT'
            else:status='OPEN_UNCERTAIN'
        return {'variable':variable,'hypothesis':f'do({variable}=1) changes P(Y=1) vs do({variable}=0)',
            'status':status,'n0':n0,'n1':n1,'effect':effect,'ci_low':low,'ci_high':high}
    def review(self):
        rows=[self.evaluate(t) for t in ('A','B')]
        with self.lab.db:
            event_count=self.lab.db.execute('SELECT COUNT(*) FROM experiment_events').fetchone()[0]
            now=datetime.now(timezone.utc).isoformat()
            for row in rows:
                self.lab.db.execute("""INSERT INTO hypothesis_reviews
                (created_utc,variable,hypothesis,status,n0,n1,effect,ci_low,ci_high,event_count)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",(now,row['variable'],row['hypothesis'],row['status'],row['n0'],row['n1'],row['effect'],row['ci_low'],row['ci_high'],event_count))
        return rows
    def history(self,n=10):
        if not isinstance(n,int) or not 1<=n<=100:raise ValueError('n must be 1..100')
        columns=('id','created_utc','variable','hypothesis','status','n0','n1','effect','ci_low','ci_high','event_count')
        return [dict(zip(columns,r)) for r in self.lab.db.execute('SELECT * FROM hypothesis_reviews ORDER BY id DESC LIMIT ?',(n,))]
    def choose(self):
        """Prioritize least-tested arm among hypotheses that are still unresolved."""
        evaluations=[self.evaluate(t) for t in ('A','B')]
        pending=[r for r in evaluations if r['status'].startswith('OPEN')]
        candidates=pending if pending else evaluations
        t=min(candidates,key=lambda r:(min(r['n0'],r['n1']),r['variable']))
        return t['variable'],0 if t['n0']<=t['n1'] else 1
    def explore(self,n=1):
        self.lab._check_n(n)
        return [self.lab._record(self.choose()) for _ in range(n)]
