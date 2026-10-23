import tempfile
import unittest
from pathlib import Path
from foundation.generalization import RelationGraph
from foundation.hierarchical_structures import build_hierarchy,reconstruct,HierarchyLab

class HierarchyTests(unittest.TestCase):
    def graph(self,ids=(1,2,3)):
        a,b,c=ids
        return RelationGraph(list(ids),[(a,'PRECEDES',b),(b,'PRECEDES',c),(c,'PRECEDES',a)])
    def test_roundtrip(self):
        t=build_hierarchy(self.graph());self.assertEqual(len(reconstruct(t)),3)
    def test_recursive_parent(self):
        t=build_hierarchy(self.graph());self.assertTrue(any(n['level']>=2 for n in t['nodes'].values()))
    def test_id_invariance(self):
        a=build_hierarchy(self.graph());b=build_hierarchy(self.graph((91,82,73)))
        self.assertEqual({n['macro_id'] for n in a['nodes'].values()},
                         {n['macro_id'] for n in b['nodes'].values()})
    def test_direction_matters(self):
        a=build_hierarchy(RelationGraph([1,2,3],[(1,'x',2),(2,'x',3)]))
        b=build_hierarchy(RelationGraph([1,2,3],[(2,'x',1),(2,'x',3)]))
        self.assertNotEqual({n['signature'] for n in a['nodes'].values()},
                            {n['signature'] for n in b['nodes'].values()})
    def test_tamper_detected(self):
        t=build_hierarchy(self.graph());t['original_edges']=[]
        with self.assertRaises(ValueError):reconstruct(t)
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'test.sqlite');lab=HierarchyLab(path)
            run,t=lab.learn('a',self.graph());lab.close()
            lab=HierarchyLab(path);self.assertEqual(reconstruct(lab.load(run)),reconstruct(t));lab.close()
    def test_shared(self):
        with tempfile.TemporaryDirectory() as d:
            lab=HierarchyLab(str(Path(d)/'x.sqlite'))
            lab.learn('a',self.graph());lab.learn('b',self.graph((91,82,73)))
            self.assertTrue(lab.shared(2));lab.close()
    def test_disconnected(self):
        g=RelationGraph([1,2,3,4],[(1,'x',2),(3,'x',4)])
        t=build_hierarchy(g);self.assertEqual(len(t['roots']),2);self.assertEqual(len(reconstruct(t)),2)
    def test_reject_empty(self):
        with self.assertRaises(ValueError):build_hierarchy(RelationGraph([1],[]))
