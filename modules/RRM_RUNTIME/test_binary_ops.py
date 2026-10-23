import unittest
from runtime import BinaryRuntime
from binary_ops import BinaryOps

def s(relation='near', a='a',b='b', extra=False):
    nodes={a:'point',b:'point'}
    edges=[[a,relation,b]]
    if extra:
        nodes['z']='signal'; edges.append(['z','red',a])
    return {'nodes':nodes,'edges':edges}

class BinaryOperationTests(unittest.TestCase):
    def setUp(self):
        self.rt=BinaryRuntime(); self.ops=BinaryOps(self.rt)
    def tearDown(self): self.rt.close()
    def test_relate_interned(self):
        a=self.rt._atom('a'); r=self.rt._atom('near'); b=self.rt._atom('b')
        self.assertEqual(self.ops.relate(a,r,b),self.ops.relate(a,r,b))
    def test_diff_and_continue(self):
        a=self.rt.store_state(s()); b=self.rt.store_state(s('far'))
        d=self.ops.diff(a,b)
        self.assertEqual(len(d),1)
        self.assertEqual(self.ops.continue_with(a,d[0]),b)
    def test_transfer_new_names_and_untouched_edge(self):
        a=self.rt.store_state(s()); b=self.rt.store_state(s('far'))
        new=self.rt.store_state(s(a='x',b='y',extra=True))
        out=self.ops.continue_with(new,self.ops.diff(a,b)[0])
        self.assertEqual(self.rt.load_state(out),s('far',a='x',b='y',extra=True))
        self.assertEqual(self.ops.diff(new,out)[0].index,0)
    def test_no_change(self):
        a=self.rt.store_state(s()); self.assertEqual(self.ops.diff(a,a),())
    def test_incompatible_nodes(self):
        a=self.rt.store_state(s()); b=self.rt.store_state(s(a='x',b='y'))
        self.assertIsNone(self.ops.diff(a,b))
    def test_guard_relation(self):
        a=self.rt.store_state(s()); b=self.rt.store_state(s('far'))
        x=self.rt.store_state(s('other'))
        with self.assertRaises(ValueError): self.ops.continue_with(x,self.ops.diff(a,b)[0])
    def test_no_observation_written(self):
        a=self.rt.store_state(s()); b=self.rt.store_state(s('far'))
        prior=self.rt.stats()['observations']
        self.ops.continue_with(a,self.ops.diff(a,b)[0])
        self.assertEqual(self.rt.stats()['observations'],prior)

if __name__=='__main__': unittest.main()
