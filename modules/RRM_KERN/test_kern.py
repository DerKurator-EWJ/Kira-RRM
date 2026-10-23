import tempfile
import unittest
from pathlib import Path
from kern import Kern

class TestKern(unittest.TestCase):
    def test_learning_and_restart(self):
        with tempfile.TemporaryDirectory() as d:
            db=str(Path(d)/'memory.sqlite')
            k=Kern(db);self.assertEqual(k.predict('x')['state'],'OPEN')
            k.observe('x','A B C A B C A B'.split())
            self.assertEqual(k.predict('x')['next'],'C')
            self.assertEqual(Kern(db).predict('x')['next'],'C')
    def test_dream_not_observation(self):
        with tempfile.TemporaryDirectory() as d:
            k=Kern(str(Path(d)/'x.sqlite'))
            k.observe('x','A B A B A'.split())
            n=len(k.events('x'))
            self.assertEqual(k.dream('x',3)['generated'],['B','A','B'])
            self.assertEqual(len(k.events('x')),n)
    def test_ambiguous(self):
        with tempfile.TemporaryDirectory() as d:
            k=Kern(str(Path(d)/'x.sqlite'),depth=1)
            k.observe('x','A B A C A'.split())
            p=k.predict('x');self.assertEqual(p['support'],2)
            self.assertEqual(p['certainty'],.5)
    def test_stream_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            k=Kern(str(Path(d)/'x.sqlite'))
            k.observe('x','A B A B A'.split())
            self.assertEqual(k.predict('y')['state'],'OPEN')

if __name__=='__main__':unittest.main()
