import tempfile
import unittest
from pathlib import Path
from rrm import RelationalCore,canonical

def frame(a='a',b='b',relation='near'):
    return {'nodes':{a:'point',b:'point'},'edges':[[a,relation,b]]}

class TestRRM(unittest.TestCase):
    def test_renaming_invariance_and_direction(self):
        self.assertEqual(canonical(frame()),canonical(frame('x','y')))
        self.assertNotEqual(canonical(frame()),canonical({'nodes':{'a':'point','b':'point'},'edges':[['a','other','b']]}))
    def test_learning_restart_and_dream_separation(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'memory.db')
            k=RelationalCore(path)
            a=frame(relation='near');b=frame(relation='far')
            for s in [a,b,a,b,a]:k.observe('vision',s)
            self.assertEqual(k.predict('vision')['next_signature'],canonical(b))
            before=k.count('vision')
            self.assertEqual(k.dream('vision',3)['signatures'],[canonical(b),canonical(a),canonical(b)])
            self.assertEqual(k.count('vision'),before)
            self.assertEqual(RelationalCore(path).predict('vision')['next_signature'],canonical(b))
    def test_open_question_is_not_surprise(self):
        with tempfile.TemporaryDirectory() as d:
            k=RelationalCore(str(Path(d)/'memory.db'))
            s=frame();self.assertEqual(k.predict('x',s)['state'],'OPEN')
            k.ask('x',s,'Warum besteht diese Beziehung?')
            self.assertEqual(k.questions('x'),[('Warum besteht diese Beziehung?','OPEN')])
    def test_stream_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            k=RelationalCore(str(Path(d)/'memory.db'))
            k.observe('a',frame());k.observe('a',frame(relation='far'))
            self.assertEqual(k.predict('b',frame())['state'],'OPEN')
    def test_bound_explicit(self):
        with self.assertRaises(ValueError):canonical({'nodes':{str(i):'n' for i in range(8)},'edges':[]})

if __name__=='__main__':unittest.main()
