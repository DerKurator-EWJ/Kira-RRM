"""RRM-MEMORY 0.1: physical placement experiment, not a new identity format.
All backends return identical immutable RRM-ID wire records by stable integer handle.
"""
import sqlite3
from collections import OrderedDict
from pathlib import Path

class RAMStore:
    def __init__(self, rows):
        self.rows = dict(rows)
        self.loads = 0
        self.bytes_loaded = 0
    def get(self, handle):
        return self.rows[handle]
    def route(self, family):
        return [k for k, v in self.rows.items() if (v[0] >> 5) == family]

class DiskStore:
    def __init__(self, path):
        self.conn = sqlite3.connect(str(path))
        self.loads = 0
        self.bytes_loaded = 0
    def get(self, handle):
        row = self.conn.execute('SELECT payload FROM records WHERE handle=?', (handle,)).fetchone()
        if row is None: raise KeyError(handle)
        self.loads += 1
        self.bytes_loaded += len(row[0])
        return row[0]
    def route(self, family):
        # Baseline scans all record headers (without loading payloads)
        return [h for h, kind in self.conn.execute('SELECT handle,kind FROM records') if kind == family]
    def close(self): self.conn.close()

class RoutedCacheStore(DiskStore):
    def __init__(self, path, budget_bytes):
        super().__init__(path)
        self.budget_bytes = budget_bytes
        self.cache = OrderedDict()
        self.used_bytes = 0
        self.hits = 0
        self.peak_bytes = 0
    def get(self, handle):
        if handle in self.cache:
            self.hits += 1
            self.cache.move_to_end(handle)
            return self.cache[handle]
        payload = super().get(handle)
        if len(payload) <= self.budget_bytes:
            while self.used_bytes + len(payload) > self.budget_bytes and self.cache:
                _, old = self.cache.popitem(last=False)
                self.used_bytes -= len(old)
            self.cache[handle] = payload
            self.used_bytes += len(payload)
            self.peak_bytes = max(self.peak_bytes, self.used_bytes)
        return payload
    def route(self, family):
        return [row[0] for row in self.conn.execute('SELECT handle FROM records WHERE kind=? ORDER BY handle', (family,))]

def make_db(path, rows):
    path = Path(path)
    if path.exists(): path.unlink()
    conn = sqlite3.connect(str(path))
    conn.execute('CREATE TABLE records (handle INTEGER PRIMARY KEY, kind INTEGER NOT NULL, payload BLOB NOT NULL)')
    conn.executemany('INSERT INTO records VALUES (?, ?, ?)', ((k, v[0] >> 5, v) for k, v in rows))
    conn.execute('CREATE INDEX idx_kind ON records(kind)')
    conn.commit()
    conn.close()
