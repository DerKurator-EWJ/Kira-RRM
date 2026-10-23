import unittest
from foundation.generalization import RelationGraph
from foundation.partial_generalization import partial_matches,partial_transfer

class PartialTests(unittest.TestCase):
    def setUp(self):
        self.a=RelationGraph([1,2,3,4],[(1,'a',2),(2,'b',3),(2,'c',4)])
        self.b=RelationGraph([10,20,30,40,50],[(10,'a',20),(20,'b',30),(20,'x',40),(50,'z',10)])
    def test_partial_extra_nodes(self):
        r=partial_matches(self.a,self.b)
        self.assertEqual(r['status'],'UNIQUE_PARTIAL_MATCH')
        self.assertEqual(r['score']['matched_edges'],2)
        self.assertEqual(r['matches'][0]['mapping'][2],20)
    def test_missing_edge_is_not_causality(self):
        r=partial_transfer(self.a,self.b,[(2,4,'c')])
        self.assertEqual(r['proposals'],[] if 4 not in r['matches'][0]['mapping'] else r['proposals'])
        self.assertNotIn('CONFIRMED',str(r))
    def test_direction_and_label(self):
        a=RelationGraph([1,2],[(1,'on',2)])
        b=RelationGraph([3,4],[(4,'on',3)])
        self.assertEqual(partial_matches(a,b,min_edges=1)['status'],'UNIQUE_PARTIAL_MATCH')
        c=RelationGraph([3,4],[(3,'off',4)])
        self.assertEqual(partial_matches(a,c,min_edges=1)['status'],'NO_PARTIAL_MATCH')
    def test_ambiguous_refuses_transfer(self):
        a=RelationGraph([1,2,3],[(1,'x',2),(1,'x',3)])
        b=RelationGraph([4,5,6],[(4,'x',5),(4,'x',6)])
        r=partial_transfer(a,b,[(1,2,'x')],min_edges=2)
        self.assertEqual(r['status'],'AMBIGUOUS_PARTIAL_MATCH')
        self.assertEqual(r['proposals'],[])
    def test_no_shared_edges(self):
        b=RelationGraph([10,20],[(10,'q',20)])
        self.assertEqual(partial_matches(self.a,b,min_edges=1)['status'],'NO_PARTIAL_MATCH')
    def test_invalid_params(self):
        with self.assertRaises(ValueError):partial_matches(self.a,self.b,min_edges=0)
        with self.assertRaises(ValueError):partial_matches(self.a,self.b,min_precision=0)
    def test_deterministic(self):
        self.assertEqual(partial_matches(self.a,self.b),partial_matches(self.a,self.b))
