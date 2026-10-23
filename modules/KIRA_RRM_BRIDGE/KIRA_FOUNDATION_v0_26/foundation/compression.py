"""Lossless hierarchical token dictionary; explicit accounting in token slots.
Research implementation, not a byte-level compressor nor a direct original port.
"""
from collections import Counter
from dataclasses import dataclass
from hashlib import blake2b
import json
import sqlite3
from pathlib import Path

@dataclass(frozen=True)
class Rule:
    id: int
    level: int
    expansion: tuple[int, ...]

class HierarchicalCompressor:
    def __init__(self, min_occurrences=3, max_width=6, max_levels=3):
        if min_occurrences < 2 or max_width < 2 or max_levels < 1:
            raise ValueError('invalid compression policy')
        self.min_occurrences=min_occurrences
        self.max_width=max_width
        self.max_levels=max_levels
        self.rules=[]

    @staticmethod
    def _replace(seq, pattern, marker):
        out=[]; count=0; i=0; n=len(pattern)
        while i<len(seq):
            if tuple(seq[i:i+n])==pattern:
                out.append(marker);count+=1;i+=n
            else:
                out.append(seq[i]);i+=1
        return out,count

    def compress(self, data):
        if any(not isinstance(x,int) or isinstance(x,bool) for x in data):
            raise TypeError('tokens must be integers')
        self.rules=[]
        seq=list(data)
        original=set(seq)
        next_marker=-1
        while next_marker in original:next_marker-=1
        for level in range(1,self.max_levels+1):
            best=None
            for width in range(2,min(self.max_width,len(seq))+1):
                counts=Counter(tuple(seq[i:i+width]) for i in range(len(seq)-width+1))
                for pattern in counts:
                    # True greedy nonoverlapping replacement, not overlapping occurrence estimate.
                    replaced,n=self._replace(seq,pattern,next_marker)
                    if n<self.min_occurrences:continue
                    # Dictionary rule uses width token slots + 1 marker header.
                    gain=len(seq)-(len(replaced)+width+1)
                    if gain<=0:continue
                    key=(gain,width,tuple(-v for v in pattern))
                    if best is None or key>best[0]:best=(key,pattern,replaced)
            if best is None:break
            _,pattern,seq=best
            self.rules.append(Rule(next_marker,level,pattern))
            next_marker-=1
            while next_marker in original:next_marker-=1
        assert self.expand(seq)==list(data)
        return seq

    def expand(self, encoded):
        mapping={r.id:r.expansion for r in self.rules}
        def walk(token,active):
            if token not in mapping:return [token]
            if token in active:raise ValueError('cyclic macro')
            out=[]
            for t in mapping[token]:out.extend(walk(t,active|{token}))
            return out
        result=[]
        for token in encoded:result.extend(walk(token,set()))
        return result

    def metrics(self,original,encoded):
        definition_slots=sum(1+len(r.expansion) for r in self.rules)
        stored_slots=len(encoded)+definition_slots
        return {'original_token_slots':len(original),'encoded_token_slots':len(encoded),
                'dictionary_token_slots':definition_slots,'total_token_slots':stored_slots,
                'net_saved_token_slots':len(original)-stored_slots,
                'compression_ratio_slots':stored_slots/len(original) if original else 1.0,
                'rules':len(self.rules)}

class ResearchState:
    """Persistent event streams and candidate counts, transactional SQLite storage."""
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS events (stream TEXT NOT NULL, ordinal INTEGER NOT NULL, token INTEGER NOT NULL, PRIMARY KEY(stream,ordinal))')
        self.db.execute('CREATE TABLE IF NOT EXISTS macro_rules (stream TEXT NOT NULL, level INTEGER NOT NULL, marker INTEGER NOT NULL, expansion TEXT NOT NULL, PRIMARY KEY(stream,marker))')
        self.db.execute('CREATE TABLE IF NOT EXISTS encoded (stream TEXT NOT NULL, ordinal INTEGER NOT NULL, token INTEGER NOT NULL, PRIMARY KEY(stream,ordinal))')
        self.db.commit()
    def observe(self,token,stream='generic:0'):
        if not isinstance(token,int) or isinstance(token,bool):raise TypeError('token must be integer')
        with self.db:
            self.db.execute('INSERT INTO events SELECT ?, COALESCE(MAX(ordinal)+1,0), ? FROM events WHERE stream=?',(stream,token,stream))
    def events(self,stream='generic:0'):
        return [r[0] for r in self.db.execute('SELECT token FROM events WHERE stream=? ORDER BY ordinal',(stream,))]
    def candidate_counts(self,stream='generic:0',min_width=2,max_width=6):
        seq=self.events(stream)
        return Counter(tuple(seq[i:i+n]) for n in range(min_width,max_width+1) for i in range(max(0,len(seq)-n+1)))
    def consolidate(self,stream='generic:0',**policy):
        c=HierarchicalCompressor(**policy)
        raw=self.events(stream)
        enc=c.compress(raw)
        with self.db:
            self.db.execute('DELETE FROM macro_rules WHERE stream=?',(stream,))
            self.db.execute('DELETE FROM encoded WHERE stream=?',(stream,))
            self.db.executemany('INSERT INTO macro_rules VALUES(?,?,?,?)',[(stream,r.level,r.id,json.dumps(r.expansion)) for r in c.rules])
            self.db.executemany('INSERT INTO encoded VALUES(?,?,?)',[(stream,i,t) for i,t in enumerate(enc)])
        return c.metrics(raw,enc)
    def restore(self,stream='generic:0'):
        rules=[Rule(marker,level,tuple(json.loads(exp))) for level,marker,exp in self.db.execute('SELECT level,marker,expansion FROM macro_rules WHERE stream=? ORDER BY level,marker DESC',(stream,))]
        encoded=[row[0] for row in self.db.execute('SELECT token FROM encoded WHERE stream=? ORDER BY ordinal',(stream,))]
        c=HierarchicalCompressor();c.rules=rules
        return c.expand(encoded)
    def close(self):self.db.close()
