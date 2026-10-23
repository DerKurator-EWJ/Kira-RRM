"""Conservative bridge: shared SQLite file and RRM record arena, legacy Foundation algorithms unchanged.
Not a unified learning engine. Object identity != structure-record handle.
"""
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for directory in ('RRM_UNIFIED_0_1','KIRA_FOUNDATION_v0_26'):
    sys.path.insert(0,str(ROOT/directory))
from binary_learning import BinaryLearningRuntime
from foundation.wiedererkennung import Wiedererkennung
from foundation.bestand import Bestand
from foundation.inquiry_queue import InquiryQueue
from foundation.staunen_bruecke import StaunenBruecke

class KiraBridge:
    def __init__(self, path, cache_budget=65536):
        if str(path)==':memory:':
            raise ValueError('Bridge needs a file path for shared persistence and queue connections')
        self.path=str(path)
        self.rrm=BinaryLearningRuntime(self.path,cache_budget=cache_budget)
        self.rrm.db.executescript('''
            CREATE TABLE IF NOT EXISTS bridge_snapshots(component TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS bridge_identity(kind TEXT NOT NULL, external_id TEXT NOT NULL,
                atom_handle INTEGER NOT NULL REFERENCES records(id), PRIMARY KEY(kind,external_id));
            CREATE TABLE IF NOT EXISTS bridge_events(id INTEGER PRIMARY KEY, stream TEXT NOT NULL,
                position INTEGER NOT NULL, state_handle INTEGER NOT NULL REFERENCES records(id),
                UNIQUE(stream,position));
        ''')
        self.rrm.db.commit()
        self.tracker=self._restore('tracker',Wiedererkennung)
        self.bestand=self._restore('bestand',Bestand)
        self.queue=InquiryQueue(self.path)
        self.staunen=StaunenBruecke(self.bestand,self.queue)

    def _restore(self, name, cls):
        row=self.rrm.db.execute('SELECT payload FROM bridge_snapshots WHERE component=?',(name,)).fetchone()
        if not row: return cls()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'snapshot.json'; p.write_text(row[0],encoding='utf-8')
            return cls.laden(p)

    def _save(self,name,obj):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'snapshot.json'; obj.speichern(p)
            payload=p.read_text(encoding='utf-8')
        self.rrm.db.execute('INSERT INTO bridge_snapshots VALUES (?,?) ON CONFLICT(component) DO UPDATE SET payload=excluded.payload',(name,payload))

    def _identity(self,kind,external_id):
        key=str(external_id)
        row=self.rrm.db.execute('SELECT atom_handle FROM bridge_identity WHERE kind=? AND external_id=?',(kind,key)).fetchone()
        if row: return row[0]
        # RRM atom is a stable record handle; namespace prevents identity collision.
        handle=self.rrm._atom(kind+':'+key)
        self.rrm.db.execute('INSERT INTO bridge_identity VALUES (?,?,?)',(kind,key,handle))
        return handle

    def recognize(self,sichten):
        """Persist Foundation tracking identity and map it to a stable RRM handle."""
        result=self.tracker.beobachten(sichten)
        with self.rrm.db:
            mapped={label:{'object_id':obj,'rrm_handle':self._identity('object',obj)} for label,obj in result.items()}
            self._save('tracker',self.tracker)
        return mapped

    def observe(self,stream,state):
        """One shared observation/evidence path; no second Foundation observation DB."""
        position=self.rrm.observe(stream,state)
        handle=self.rrm.db.execute('SELECT state_id FROM observations WHERE stream=? AND position=?',(stream,position)).fetchone()[0]
        with self.rrm.db:
            self.rrm.db.execute('INSERT INTO bridge_events(stream,position,state_handle) VALUES (?,?,?)',(stream,position,handle))
        return {'position':position,'state_handle':handle}

    def relationships(self,anwesend,gekoppelt=(),gemeinsam_bewegt=()):
        result=self.staunen.beobachten(anwesend,gekoppelt,gemeinsam_bewegt)
        with self.rrm.db:
            for name in anwesend: self._identity('object',name)
            self._save('bestand',self.bestand)
        return result

    def identity_handle(self,kind,external_id):
        row=self.rrm.db.execute('SELECT atom_handle FROM bridge_identity WHERE kind=? AND external_id=?',(kind,str(external_id))).fetchone()
        return row[0] if row else None

    def close(self):
        self.queue.close()
        self.rrm.close()
