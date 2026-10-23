"""Data-driven candidate discovery; intervention is separate from observational screening."""
import math
from datetime import datetime,timezone
from .hypotheses import HypothesisEngine

class DiscoveryEngine:
    def __init__(self,lab,minimum_observations=30,association_threshold=.08,minimum_per_arm=30):
        self.lab=lab
        self.minimum_observations=int(minimum_observations)
        self.association_threshold=float(association_threshold)
        if self.minimum_observations<1 or not 0<=self.association_threshold<=1:raise ValueError('invalid discovery settings')
        self.evidence=HypothesisEngine(lab,minimum_per_arm=minimum_per_arm)
        lab.db.execute("""CREATE TABLE IF NOT EXISTS discovered_hypotheses(
          variable TEXT PRIMARY KEY, outcome TEXT NOT NULL, discovered_utc TEXT NOT NULL,
          observational_n INTEGER NOT NULL, association REAL NOT NULL, status TEXT NOT NULL)""")
        lab.db.execute("""CREATE TABLE IF NOT EXISTS discovery_reviews(
          id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT NOT NULL,
          variable TEXT NOT NULL, status TEXT NOT NULL, effect REAL, ci_low REAL, ci_high REAL,
          n0 INTEGER NOT NULL,n1 INTEGER NOT NULL)""")
        lab.db.commit()

    def eligible_variables(self):
        # Variables are discovered from observed columns, not enumerated as hypotheses.
        columns=[r[1] for r in self.lab.db.execute('PRAGMA table_info(experiment_events)')]
        return [c for c in columns if c.lower() not in ('id','kind','target','value','y') and c.lower() in ('a','b')]

    def scan(self):
        found=[]
        for col in self.eligible_variables():
            arms=[self.lab.db.execute(f"""SELECT COUNT(*),COALESCE(SUM(y),0)
                FROM experiment_events WHERE kind='observe' AND "{col}"=?""",(v,)).fetchone() for v in (0,1)]
            (n0,s0),(n1,s1)=arms
            if min(n0,n1)<self.minimum_observations:continue
            association=s1/n1-s0/n0
            if abs(association)<self.association_threshold:continue
            variable=col.upper()
            with self.lab.db:
                self.lab.db.execute("""INSERT OR IGNORE INTO discovered_hypotheses
                    (variable,outcome,discovered_utc,observational_n,association,status)
                    VALUES(?,?,?,?,?,?)""",(variable,'Y',datetime.now(timezone.utc).isoformat(),n0+n1,association,'UNTESTED'))
            found.append(variable)
        return found

    def candidates(self):
        return [dict(zip(('variable','outcome','discovered_utc','observational_n','association','status'),r))
                for r in self.lab.db.execute('SELECT * FROM discovered_hypotheses ORDER BY variable')]

    def choose(self):
        rows=self.candidates()
        if not rows: return None
        # Prioritize open candidates, then the least tested intervention arm.
        options=[]
        for row in rows:
            result=self.evidence.evaluate(row['variable'])
            if result['status'].startswith('OPEN') or row['status']=='UNTESTED':
                options.append((min(result['n0'],result['n1']),row['variable'],0 if result['n0']<=result['n1'] else 1))
        if not options:return None
        _,variable,arm=min(options)
        return variable,arm

    def explore(self,n=1):
        self.lab._check_n(n)
        out=[]
        for _ in range(n):
            choice=self.choose()
            if choice is None:break
            out.append(self.lab._record(choice))
        return out

    def review(self):
        results=[]
        for candidate in self.candidates():
            row=self.evidence.evaluate(candidate['variable'])
            with self.lab.db:
                self.lab.db.execute('UPDATE discovered_hypotheses SET status=? WHERE variable=?',(row['status'],row['variable']))
                self.lab.db.execute("""INSERT INTO discovery_reviews
                  (created_utc,variable,status,effect,ci_low,ci_high,n0,n1) VALUES(?,?,?,?,?,?,?,?)""",
                  (datetime.now(timezone.utc).isoformat(),row['variable'],row['status'],row['effect'],row['ci_low'],row['ci_high'],row['n0'],row['n1']))
            results.append(row)
        return results

    def history(self,n=10):
        if not isinstance(n,int) or not 1<=n<=100:raise ValueError('n must be 1..100')
        cols=('id','created_utc','variable','status','effect','ci_low','ci_high','n0','n1')
        return [dict(zip(cols,r)) for r in self.lab.db.execute('SELECT * FROM discovery_reviews ORDER BY id DESC LIMIT ?',(n,))]
