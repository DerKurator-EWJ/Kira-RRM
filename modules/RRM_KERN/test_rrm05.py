import os
import tempfile
import unittest
from rrm05 import Kernel, changes


def state(rel, signal='red', a='a', b='b', c='c'):
    return {'nodes':{a:'point',b:'point',c:'signal'}, 'edges':[[a,rel,b],[c,signal,a]]}


class KernelTests(unittest.TestCase):
    def test_transfer_across_names(self):
        k=Kernel()
        for s in [state('near'),state('far'),state('near'),state('far'),state('near')]: k.observe('x',s)
        result=k.predict('x',state('near',a='u',b='v',c='w'),focus=0)
        self.assertEqual(result['result']['edges'][0][1],'far')

    def test_one_store_both_projection_modes(self):
        k=Kernel()
        for rel, sig in [('near','red'),('far','red'),('near','red'),('far','red'),('near','red')]: k.observe('x',state(rel,sig))
        self.assertEqual(k.predict('x',state('near','red'),focus=0)['status'],'HYPOTHESIS')
        self.assertEqual(k.predict('x',state('near','blue'),focus=0)['status'],'OPEN')
        self.assertEqual(k.predict('x',state('near','blue'),focus=0,contextual=False)['status'],'HYPOTHESIS')

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,'store.sqlite')
            k=Kernel(p)
            for rel in ['near','far','near','far','near']: k.observe('x',state(rel))
            k.close()
            k=Kernel(p)
            self.assertEqual(k.predict('x',state('near'),focus=0)['status'],'HYPOTHESIS')
            k.close()

    def test_dream_not_observation(self):
        k=Kernel()
        for rel in ['near','far','near','far','near']: k.observe('x',state(rel))
        before=k.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
        k.dream('x',state('near'),focus=0)
        self.assertEqual(before,k.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0])

    def test_unaligned_is_rejected(self):
        a=state('near'); b=state('far'); b['edges'][1][1]='blue'
        self.assertEqual(changes(a,b),[])

    def test_tie_open(self):
        k=Kernel()
        for rel in ['near','far','near','distant','near']: k.observe('x',state(rel))
        self.assertEqual(k.predict('x',state('near'),focus=0)['status'],'OPEN')

    def test_unseen_stays_open(self):
        k=Kernel()
        self.assertEqual(k.predict('x',state('near'),focus=0)['status'],'OPEN')

if __name__=='__main__': unittest.main()
