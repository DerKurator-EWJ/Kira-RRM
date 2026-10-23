import tempfile
import unittest
from pathlib import Path
from foundation.generalization import RelationGraph
from foundation.partial_macro_routing import PartialMacroRouter,partial_plan,verify_plan,embeddings

def g(edges):return RelationGraph(sorted({v for a,_,b in edges for v in (a,b)}),edges)
class PartialRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.r=PartialMacroRouter(str(Path(self.tmp.name)/'p.sqlite'))
    def tearDown(self):self.r.close();self.tmp.cleanup()
    def test_partial_reuse(self):
        self.r.register(g([(1,'x',2),(2,'x',3)]))
        _,p=self.r.learn('new',g([(9,'x',8),(8,'x',7),(7,'x',6)]))
        self.assertEqual((p['reused_edge_count'],p['fresh_edge_count']),(2,1))
    def test_roundtrip(self):
        self.r.register(g([(1,'x',2)]))
        run,p=self.r.learn('a',g([(9,'x',8),(8,'y',7)]))
        self.assertEqual(verify_plan(self.r.load(run)),verify_plan(p))
    def test_restart(self):
        self.r.register(g([(1,'x',2)]));path=self.r.db.execute('PRAGMA database_list').fetchone()[2]
        self.r.close();self.r=PartialMacroRouter(path)
        self.assertEqual(self.r.learn('a',g([(4,'x',5)]))[1]['reused_edge_count'],1)
    def test_label_direction(self):
        self.r.register(g([(1,'x',2),(2,'y',3)]))
        p=self.r.learn('a',g([(4,'x',5),(5,'x',6)]))[1]
        self.assertEqual(p['reused_edge_count'],0)
    def test_no_overlaps(self):
        self.r.register(g([(1,'x',2)]))
        p=self.r.learn('a',g([(3,'x',4),(4,'x',5)]))[1]
        self.assertEqual(p['reused_edge_count'],2)
        verify_plan(p)
    def test_determinism(self):
        self.r.register(g([(1,'x',2)]));target=g([(3,'x',4),(4,'x',5)])
        self.assertEqual(partial_plan(target,self.r.templates()),partial_plan(target,self.r.templates()))
    def test_bad_witness_rejected(self):
        with self.assertRaises(ValueError):verify_plan({'original_edges':[[1,'x',2]],'reused':[], 'fresh_edges':[]})
    def test_template_dedup(self):
        a=self.r.register(g([(1,'x',2)]));b=self.r.register(g([(4,'x',5)]))
        self.assertEqual(a,b)
    def test_missing_run(self):
        with self.assertRaises(KeyError):self.r.load(999)
