import sqlite3,tempfile,unittest
from pathlib import Path
from foundation.prediction import TransitionPredictor
from foundation.live import LiveRuntime

class PredictionTests(unittest.TestCase):
    def test_learning_and_surprise(self):
        db=sqlite3.connect(':memory:');p=TransitionPredictor(db,'x')
        seq=[1,2,3,1,2,3,1,2,4]
        for i,token in enumerate(seq):p.record(i+1,seq[max(0,i-3):i],token)
        d=p.distribution([1,2]);self.assertEqual(d['predictions'][0]['token'],3)
        self.assertEqual(d['samples'],3)
        self.assertAlmostEqual(d['predictions'][0]['probability'],2/3)
        self.assertGreater(p.metrics()['scored_predictions'],0)
        self.assertTrue(any(row['correct'] is False for row in p.recent(20)))
    def test_prequential_no_leak(self):
        db=sqlite3.connect(':memory:');p=TransitionPredictor(db,'x')
        self.assertIsNone(p.record(1,[],7)['predicted'])
        self.assertIsNone(p.record(2,[7],8)['predicted'])
        self.assertEqual(p.record(3,[7],8)['predicted'],8)
    def test_stream_isolation(self):
        db=sqlite3.connect(':memory:');a=TransitionPredictor(db,'a');b=TransitionPredictor(db,'b')
        a.record(1,[5],7);self.assertEqual(b.distribution([5])['samples'],0)
    def test_live_restart_and_atomic_prediction(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'live.sqlite';r=LiveRuntime(path,frame_size=8);r.resume()
            for _ in range(7):r.step([100,-100]*4)
            self.assertEqual(r.status()['prediction']['observations'],7)
            before=r.predict();r.close()
            r=LiveRuntime(path,frame_size=8)
            self.assertEqual(before,r.predict());self.assertEqual(r.status()['prediction']['observations'],7)
            r.resume();r.step([100,-100]*4)
            self.assertEqual(r.status()['prediction']['observations'],8)
            r.close()
if __name__=='__main__':unittest.main()
