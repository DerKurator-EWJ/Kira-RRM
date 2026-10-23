import tempfile
import unittest
import sqlite3
from pathlib import Path
from foundation.event_graph import EventGraphLab

class EventGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'g.sqlite';self.lab=EventGraphLab(self.path)
    def tearDown(self):self.lab.close();self.tmp.cleanup()
    def test_temporal_not_causal(self):
        self.lab.ingest('a',[1,2,1,2,1,2]); e=self.lab.evidence('a')
        self.assertTrue(e['edges']);self.assertTrue(all(not x['causal'] and x['evidence']=='OBSERVATIONAL_TEMPORAL' for x in e['edges']))
    def test_restart(self):
        self.lab.ingest('a',[1,2,1,2]);self.lab.close();self.lab=EventGraphLab(self.path)
        self.assertEqual(self.lab.evidence('a')['events'],4)
    def test_stream_isolation(self):
        self.lab.ingest('a',[1,2,1,2]);self.lab.ingest('b',[7,8])
        self.assertEqual(self.lab.evidence('b')['nodes'],[7,8])
    def test_analogy_different_ids(self):
        self.lab.ingest('a',[1,2,3]*5);self.lab.ingest('b',[91,82,73]*5)
        self.assertIn(self.lab.compare('a','b')['status'],('UNIQUE_PARTIAL_MATCH','AMBIGUOUS_PARTIAL_MATCH'))
    def test_no_empty_graph(self):self.assertIsNone(self.lab.graph('missing'))
    def test_snapshot(self):
        self.lab.ingest('a',[1,2,1,2]);self.lab.snapshot('a')
        self.assertEqual(self.lab.db.execute('SELECT COUNT(*) FROM graph_snapshots').fetchone()[0],1)
    def test_import_live_idempotent(self):
        live=Path(self.tmp.name)/'live.sqlite';db=sqlite3.connect(live)
        db.execute('CREATE TABLE live_events(stream TEXT,tick INTEGER,token INTEGER,created INTEGER)')
        db.executemany('INSERT INTO live_events VALUES(?,?,?,0)',[('audio:live',1,5),('audio:live',2,6)])
        db.commit();db.close()
        self.assertEqual(self.lab.import_live(live),2)
        self.assertEqual(self.lab.import_live(live),0)
    def test_reject_bad_token(self):
        with self.assertRaises(ValueError):self.lab.ingest('a',[True])
