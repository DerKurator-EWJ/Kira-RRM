import tempfile
import unittest
from pathlib import Path
from foundation.generalization import RelationGraph
from foundation.hierarchical_structures import reconstruct,canonical_edges
from foundation.integrated_routing import IntegratedRouter,build_integrated,benchmark_equal_workload

def graph(edges):
    return RelationGraph(sorted({v for a,_,b in edges for v in (a,b)}),edges)

class IntegratedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/'integrated.sqlite')
        self.base=graph([(1,'PRECEDES',2),(2,'PRECEDES',3)])
        self.ext=graph([(91,'PRECEDES',82),(82,'PRECEDES',73),(73,'PRECEDES',64)])
    def tearDown(self):self.tmp.cleanup()
    def test_partial_reuse_is_hierarchy(self):
        r=build_integrated(self.ext,[(1,self.base.edges)])
        self.assertEqual(r['reused_edges'],2)
        self.assertEqual(r['fresh_edges'],1)
        self.assertEqual(r['new_merges'],1)
        self.assertEqual(reconstruct(r['tree']),canonical_edges(self.ext.edges))
    def test_empty_templates(self):
        r=build_integrated(self.ext,[])
        self.assertEqual(r['reused_edges'],0)
        self.assertEqual(reconstruct(r['tree']),canonical_edges(self.ext.edges))
    def test_persistence(self):
        lab=IntegratedRouter(self.path)
        lab.register(self.base)
        rid,r=lab.learn('stream',self.ext,False)
        lab.close()
        lab=IntegratedRouter(self.path)
        self.assertEqual(lab.load(rid)['reused_edges'],2)
        lab.close()
    def test_direction_is_preserved(self):
        reversed_graph=graph([(91,'PRECEDES',82),(73,'PRECEDES',82),(73,'PRECEDES',64)])
        r=build_integrated(reversed_graph,[(1,self.base.edges)])
        self.assertEqual(reconstruct(r['tree']),canonical_edges(reversed_graph.edges))
    def test_no_double_cover(self):
        r=build_integrated(self.ext,[(1,self.base.edges),(2,self.base.edges)])
        self.assertEqual(r['reused_edges'],2)
    def test_equal_workload(self):
        result=benchmark_equal_workload(self.ext,[(1,self.base.edges)],3)
        self.assertIn('baseline_ms',result)
        self.assertIn('integrated_ms',result)
    def test_invalid_stream(self):
        lab=IntegratedRouter(self.path)
        with self.assertRaises(ValueError):lab.learn('',self.ext)
        lab.close()
