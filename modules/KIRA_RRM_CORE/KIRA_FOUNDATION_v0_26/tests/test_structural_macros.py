import os
import tempfile
import unittest
from foundation.generalization import RelationGraph
from foundation.structural_macros import canonical_motif,motifs,StructuralMacroLab
from foundation.event_graph import EventGraphLab

class StructuralTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.lab=StructuralMacroLab(os.path.join(self.tmp.name,'macro.sqlite'))
    def tearDown(self):
        self.lab.close();self.tmp.cleanup()
    def test_id_invariance(self):
        self.assertEqual(canonical_motif([(1,'PRECEDES',2),(2,'PRECEDES',3)]),
                         canonical_motif([(90,'PRECEDES',80),(80,'PRECEDES',70)]))
    def test_direction_matters(self):
        self.assertNotEqual(canonical_motif([(1,'X',2),(2,'X',3)]),
                            canonical_motif([(1,'X',2),(3,'X',2)]))
    def test_relation_type_matters(self):
        self.assertNotEqual(canonical_motif([(1,'X',2)]),canonical_motif([(1,'Y',2)]))
    def test_shared_macro(self):
        a=RelationGraph([1,2,3],[(1,'X',2),(2,'Y',3)])
        b=RelationGraph([10,20,30],[(10,'X',20),(20,'Y',30)])
        self.lab.learn('a',a);self.lab.learn('b',b)
        shared=self.lab.shared(['a','b'])
        self.assertEqual(len(shared),1)
        self.assertEqual(shared[0]['edges'],2)
        self.assertEqual(shared[0]['streams'],2)
    def test_different_structures_not_shared(self):
        self.lab.learn('a',RelationGraph([1,2,3],[(1,'X',2),(2,'Y',3)]))
        self.lab.learn('b',RelationGraph([4,5,6],[(4,'X',5),(5,'Z',6)]))
        self.assertEqual(self.lab.shared(['a','b']),[])
    def test_repeat_learning_idempotent(self):
        g=RelationGraph([1,2,3],[(1,'X',2),(2,'Y',3)])
        self.lab.learn('a',g);self.lab.learn('a',g)
        self.lab.learn('b',g)
        self.assertEqual(self.lab.shared(['a','b'])[0]['streams'],2)
    def test_persistence(self):
        path=os.path.join(self.tmp.name,'persist.sqlite')
        a=RelationGraph([1,2,3],[(1,'X',2),(2,'Y',3)])
        one=StructuralMacroLab(path);one.learn('a',a);one.close()
        two=StructuralMacroLab(path);two.learn('b',a)
        self.assertEqual(len(two.shared(['a','b'])),1)
        two.close()
    def test_event_graph_integration(self):
        events=EventGraphLab(os.path.join(self.tmp.name,'events.sqlite'))
        for stream,seq in [('a',[1,2,3]*5),('b',[10,20,30]*5)]:
            events.ingest(stream,seq)
            self.lab.learn(stream,events.graph(stream))
        self.assertTrue(self.lab.shared(['a','b']))
        events.close()
    def test_invalid(self):
        with self.assertRaises(ValueError):canonical_motif([])
        with self.assertRaises(ValueError):self.lab.shared(['only'])
