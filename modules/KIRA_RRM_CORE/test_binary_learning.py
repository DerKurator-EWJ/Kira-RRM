import tempfile,unittest
from pathlib import Path
from bridge import KiraBridge

class BinaryLearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'core.db')
        self.k=KiraBridge(self.path)
    def tearDown(self):
        self.k.close();self.tmp.cleanup()
    def state(self,rel,names=('a','b'),extra=False):
        a,b=names
        nodes={a:'point',b:'point'}
        edges=[[a,rel,b]]
        if extra:
            nodes['c']='point';edges.append(['c','tag',a])
        return {'nodes':nodes,'edges':edges}
    def test_learning_and_transfer(self):
        for _ in range(3):
            self.k.observe('x',self.state('near'))
            self.k.observe('x',self.state('far'))
        p=self.k.rrm.predict('x',self.state('near',('u','v')),contextual=False)
        self.assertEqual(p['result'],self.state('far',('u','v')))
        self.assertEqual(self.k.rrm.db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],0)
    def test_restart_and_dream(self):
        for _ in range(3):
            self.k.observe('x',self.state('near'))
            self.k.observe('x',self.state('far'))
        n=self.k.rrm.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
        self.k.rrm.dream('x',self.state('near'),steps=3,contextual=False)
        self.assertEqual(self.k.rrm.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],n)
        self.k.close();self.k=KiraBridge(self.path)
        self.assertEqual(self.k.rrm.predict('x',self.state('near'),contextual=False)['result'],self.state('far'))
    def test_context_and_unknown(self):
        for _ in range(3):
            self.k.observe('red',self.state('near',extra=True))
            self.k.observe('red',self.state('far',extra=True))
        p=self.k.rrm.predict('red',self.state('near',extra=True))
        self.assertEqual(p['status'],'HYPOTHESIS')
        self.assertEqual(p['result'],self.state('far',extra=True))
        self.assertEqual(self.k.rrm.predict('red',self.state('near'))['status'],'OPEN')
    def test_ambiguous(self):
        for next_rel in ('far','other','far','other'):
            self.k.observe('a',self.state('near'))
            self.k.observe('a',self.state(next_rel))
        p=self.k.rrm.predict('a',self.state('near'),contextual=False,min_support=1)
        self.assertEqual(p['status'],'OPEN')

if __name__=='__main__':unittest.main()
