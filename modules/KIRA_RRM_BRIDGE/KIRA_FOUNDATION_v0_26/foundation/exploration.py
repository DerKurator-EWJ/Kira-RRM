# Controlled intervention laboratory; association is not intervention effect.
import hashlib, json, sqlite3
from pathlib import Path

class ToyWorld:
    """A correlates with outcome due to hidden Z; B changes the outcome.
    Exogenous variables are deterministic per experiment number and seed, not Python hash().
    """
    def __init__(self, seed=7): self.seed=int(seed)
    def _draw(self, index, channel):
        raw=f'{self.seed}:{index}:{channel}'.encode()
        return int.from_bytes(hashlib.blake2b(raw,digest_size=8).digest(),'big')/2**64
    def sample(self,index,do=None):
        if do is not None and (len(do)!=2 or do[0] not in ('A','B') or do[1] not in (0,1)):
            raise ValueError('intervention must be (A|B, 0|1)')
        z=int(self._draw(index,'z')<0.5)
        a=z if self._draw(index,'a')<0.9 else 1-z
        b=int(self._draw(index,'b')<0.5)
        if do is not None:
            if do[0]=='A':a=do[1]
            else:b=do[1]
        # P(Y=1|Z,B) = .10 + .35*Z + .45*B ; A has no direct effect.
        y=int(self._draw(index,'y') < 0.10+0.35*z+0.45*b)
        return {'A':a,'B':b,'Y':y}, {'Z':z} # hidden information never stored in learner

class ExplorationLab:
    def __init__(self,path='data/exploration.sqlite',seed=7):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS experiment_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS experiment_events(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,target TEXT,value INTEGER, a INTEGER NOT NULL,b INTEGER NOT NULL,y INTEGER NOT NULL);
        """)
        self.world=ToyWorld(seed)
        saved=self.db.execute("SELECT value FROM experiment_meta WHERE key='seed'").fetchone()
        if saved is not None and int(saved[0])!=seed:raise ValueError('existing experiment seed differs')
        if saved is None:
            with self.db:self.db.execute("INSERT INTO experiment_meta VALUES('seed',?)",(str(seed),))
    def _next(self):return self.db.execute('SELECT COALESCE(MAX(id),0)+1 FROM experiment_events').fetchone()[0]
    def observe(self,n=1):
        self._check_n(n)
        for _ in range(n):self._record(None)
    @staticmethod
    def _check_n(n):
        if not isinstance(n,int) or not 0<=n<=100000:raise ValueError('n must be 0..100000')
    def _record(self,intervention):
        index=self._next(); observed,_hidden=self.world.sample(index,intervention)
        target,value=intervention if intervention else (None,None)
        with self.db:
            self.db.execute('INSERT INTO experiment_events VALUES(?,?,?,?,?,?,?)',
                (index,'do' if intervention else 'observe',target,value,observed['A'],observed['B'],observed['Y']))
        return {'id':index,'kind':'do' if intervention else 'observe','target':target,'value':value,**observed}
    def intervene(self,target,value,n=1):
        self._check_n(n)
        if target not in ('A','B') or value not in (0,1):raise ValueError('use A|B and 0|1')
        return [self._record((target,value)) for _ in range(n)]
    def choose(self):
        # Balanced exploration: select least-sampled intervention arm, stable tie-break.
        counts={(t,v):0 for t in ('A','B') for v in (0,1)}
        for t,v,n in self.db.execute("SELECT target,value,COUNT(*) FROM experiment_events WHERE kind='do' GROUP BY target,value"):
            counts[t,v]=n
        return min(counts,key=lambda k:(counts[k],k[0],k[1]))
    def explore(self,n=1):
        self._check_n(n)
        return [self._record(self.choose()) for _ in range(n)]
    def report(self):
        out={'observations':self.db.execute("SELECT COUNT(*) FROM experiment_events WHERE kind='observe'").fetchone()[0],
             'interventions':self.db.execute("SELECT COUNT(*) FROM experiment_events WHERE kind='do'").fetchone()[0],
             'variables':{}}
        for t in ('A','B'):
            arms=[]
            for v in (0,1):
                # Observational conditional vs intervention: distinct samples, no mixing.
                field=t.lower()
                n,s=self.db.execute(f"SELECT COUNT(*),COALESCE(SUM(y),0) FROM experiment_events WHERE kind='observe' AND {field}=?",(v,)).fetchone()
                dn,ds=self.db.execute("SELECT COUNT(*),COALESCE(SUM(y),0) FROM experiment_events WHERE kind='do' AND target=? AND value=?",(t,v)).fetchone()
                arms.append({'value':v,'observational':{'n':n,'p_y':s/n if n else None},
                             'interventional':{'n':dn,'p_y':ds/dn if dn else None}})
            obs=[x['observational']['p_y'] for x in arms]
            inter=[x['interventional']['p_y'] for x in arms]
            out['variables'][t]={'arms':arms,'association_difference':obs[1]-obs[0] if None not in obs else None,
                                 'intervention_difference':inter[1]-inter[0] if None not in inter else None}
        return out
    def recent(self,n=5):
        if not 1<=n<=100:raise ValueError('n must be 1..100')
        return [dict(zip(('id','kind','target','value','A','B','Y'),r)) for r in self.db.execute('SELECT * FROM experiment_events ORDER BY id DESC LIMIT ?',(n,))]
    def close(self):self.db.close()
