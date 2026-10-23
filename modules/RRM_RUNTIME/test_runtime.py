import os,tempfile,unittest
from runtime import BinaryRuntime
from rrm05 import Kernel

def state(rel='near',signal='red',a='a',b='b',c='c'):
    return {'nodes':{a:'point',b:'point',c:'signal'},'edges':[[a,rel,b],[c,signal,a]]}

class RuntimeTests(unittest.TestCase):
    def test_roundtrip_and_interning(self):
        k=BinaryRuntime(); a=k.store_state(state()); b=k.store_state(state())
        self.assertEqual(a,b); self.assertEqual(k.load_state(a),state()); k.close()
    def test_isolated_node(self):
        k=BinaryRuntime(); s={'nodes':{'x':'point'},'edges':[]}; self.assertEqual(k.load_state(k.store_state(s)),s)
    def test_unicode_and_odd_bits(self):
        k=BinaryRuntime(); s=state('nähe','grün'); self.assertEqual(k.load_state(k.store_state(s)),s)
    def test_prediction_parity(self):
        a=BinaryRuntime(); b=Kernel()
        for r in ('near','far','near','far','near'):
            a.observe('x',state(r)); b.observe('x',state(r))
        for contextual in (True,False):
            self.assertEqual(a.predict('x',state(),focus=0,contextual=contextual),b.predict('x',state(),focus=0,contextual=contextual))
    def test_dream_no_learning(self):
        k=BinaryRuntime()
        for r in ('near','far','near','far','near'): k.observe('x',state(r))
        before=k.stats(); self.assertTrue(k.dream('x',state(),focus=0)); self.assertEqual(before,k.stats())
    def test_restart_and_handle(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'r.sqlite'); k=BinaryRuntime(path)
            for r in ('near','far','near','far','near'): k.observe('x',state(r))
            handle=k.store_state(state()); k.close(); k=BinaryRuntime(path)
            self.assertEqual(k.load_state(handle),state())
            self.assertEqual(k.predict('x',handle,focus=0)['result']['edges'][0][1],'far'); k.close()
    def test_context_open(self):
        k=BinaryRuntime()
        for r in ('near','far','near','far','near'): k.observe('x',state(r))
        self.assertEqual(k.predict('x',state(signal='blue'),focus=0)['status'],'OPEN')
        self.assertEqual(k.predict('x',state(signal='blue'),focus=0,contextual=False)['status'],'HYPOTHESIS')
    def test_distinct_names_are_distinct_states(self):
        k=BinaryRuntime(); self.assertNotEqual(k.store_state(state()),k.store_state(state(a='u',b='v',c='w')))

if __name__=='__main__': unittest.main()
