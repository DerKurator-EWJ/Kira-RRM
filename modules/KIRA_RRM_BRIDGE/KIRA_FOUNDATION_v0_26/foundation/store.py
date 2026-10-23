"""Small auditable SQLite research store; not a port of Android storage."""
import sqlite3
from pathlib import Path
from .ids import stable_id
class Store:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('CREATE TABLE IF NOT EXISTS identities(scheme TEXT NOT NULL, numeric_id INTEGER NOT NULL, namespace TEXT NOT NULL, symbol TEXT NOT NULL, PRIMARY KEY(scheme,numeric_id), UNIQUE(scheme,namespace,symbol));\nCREATE TABLE IF NOT EXISTS triples(id INTEGER PRIMARY KEY AUTOINCREMENT, scheme TEXT NOT NULL, subject INTEGER NOT NULL, predicate INTEGER NOT NULL, object INTEGER NOT NULL, UNIQUE(scheme,subject,predicate,object));\nCREATE INDEX IF NOT EXISTS triples_subject ON triples(scheme,subject,predicate);')
        self.db.commit()
    def identity(self,namespace,symbol,scheme='forge'):
        numeric=stable_id(namespace,symbol,scheme)
        existing=self.db.execute('SELECT namespace,symbol FROM identities WHERE scheme=? AND numeric_id=?',(scheme,numeric)).fetchone()
        if existing and existing!=(namespace,symbol): raise ValueError('ID collision detected')
        self.db.execute('INSERT OR IGNORE INTO identities VALUES(?,?,?,?)',(scheme,numeric,namespace,symbol))
        self.db.commit()
        return numeric
    def relate(self,s,p,o,scheme='forge'):
        ids=(self.identity('node',s,scheme),self.identity('relation',p,scheme),self.identity('node',o,scheme))
        self.db.execute('INSERT OR IGNORE INTO triples(scheme,subject,predicate,object) VALUES(?,?,?,?)',(scheme,*ids));self.db.commit()
        return ids
    def outgoing(self,s,scheme='forge'):
        sid=self.identity('node',s,scheme)
        return self.db.execute('SELECT p.symbol,o.symbol FROM triples t JOIN identities p ON p.scheme=t.scheme AND p.numeric_id=t.predicate JOIN identities o ON o.scheme=t.scheme AND o.numeric_id=t.object WHERE t.scheme=? AND t.subject=? ORDER BY p.symbol,o.symbol',(scheme,sid)).fetchall()
    def close(self):self.db.close()
