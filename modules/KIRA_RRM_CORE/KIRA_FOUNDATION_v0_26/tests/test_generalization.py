import tempfile
import unittest
from pathlib import Path
from foundation.generalization import RelationGraph, mappings, transfer, GeneralizationStore

class GeneralizationTests(unittest.TestCase):
    def setUp(self):
        self.a=RelationGraph([1,2,3,4],[(1,'on',2),(2,'on',3),(2,'off',4)])
        self.b=RelationGraph([80,70,60,50],[(80,'on',70),(70,'on',60),(70,'off',50)])

    def test_unique_renaming(self):
        self.assertEqual(mappings(self.a,self.b),[{1:80,2:70,3:60,4:50}])

    def test_transfer_is_unverified(self):
        result=transfer(self.a,self.b,[(2,4,'off')])
        self.assertEqual(result['status'],'UNIQUE_MATCH')
        self.assertEqual(result['proposals'],[{'source':70,'target':50,'relation':'off','status':'UNVERIFIED_TRANSFER'}])

    def test_direction_matters(self):
        changed=RelationGraph([80,70,60,50],[(70,'on',80),(70,'on',60),(70,'off',50)])
        self.assertEqual(transfer(self.a,changed,[])['status'],'NO_MATCH')

    def test_relation_matters(self):
        changed=RelationGraph([80,70,60,50],[(80,'on',70),(70,'on',60),(70,'on',50)])
        self.assertEqual(transfer(self.a,changed,[])['status'],'NO_MATCH')

    def test_ambiguity_is_rejected(self):
        a=RelationGraph([1,2],[(1,'link',2),(2,'link',1)])
        b=RelationGraph([3,4],[(3,'link',4),(4,'link',3)])
        self.assertEqual(transfer(a,b,[(1,2,'link')])['status'],'AMBIGUOUS')

    def test_invalid_proposal(self):
        with self.assertRaises(ValueError):transfer(self.a,self.b,[(1,4,'on')])

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'graph.sqlite'
            store=GeneralizationStore(path)
            result=transfer(self.a,self.b,[(2,4,'off')])
            store.record(self.a,self.b,result);store.close()
            store=GeneralizationStore(path)
            self.assertEqual(store.history()[0]['result']['proposals'],result['proposals'])
            store.close()

    def test_node_limit_and_missing_endpoint(self):
        with self.assertRaises(ValueError):RelationGraph(list(range(8)),[])
        with self.assertRaises(ValueError):RelationGraph([1],[(1,'on',2)])
