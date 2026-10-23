import tempfile,unittest
from pathlib import Path
from foundation.exploration import ExplorationLab
from foundation.hypotheses import HypothesisEngine
class HypothesisTests(unittest.TestCase):
    def make(self,tmp):
        lab=ExplorationLab(str(Path(tmp)/'hyp.sqlite'))
        return lab,HypothesisEngine(lab)
    def test_initially_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab,h=self.make(tmp)
            self.assertEqual(h.evaluate('A')['status'],'OPEN_INSUFFICIENT_EVIDENCE')
            with self.assertRaises(ValueError):h.evaluate('Z')
            lab.close()
    def test_choose_balanced(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab,h=self.make(tmp)
            self.assertEqual(h.choose(),('A',0))
            h.explore(80)
            counts=[h.evaluate(t)[f'n{v}'] for t in ('A','B') for v in (0,1)]
            self.assertEqual(counts,[20]*4)
            lab.close()
    def test_effects_and_non_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab,h=self.make(tmp)
            lab.observe(3000);h.explore(4000)
            a,b=h.evaluate('A'),h.evaluate('B')
            self.assertEqual(a['status'],'SUPPORTED_NEGLIGIBLE_EFFECT')
            self.assertEqual(b['status'],'SUPPORTED_POSITIVE_EFFECT')
            self.assertGreater(b['ci_low'],0.10)
            lab.close()
    def test_review_persists_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab,h=self.make(tmp);lab.explore(200);h.review();lab.close()
            lab,h=self.make(tmp)
            self.assertEqual(len(h.history()),2)
            self.assertEqual(h.history()[0]['event_count'],200)
            lab.close()
    def test_review_is_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab,h=self.make(tmp);h.review();old=h.history()[0]
            h.explore(200);h.review()
            self.assertEqual(old['event_count'],0)
            self.assertEqual(h.history()[0]['event_count'],200)
            lab.close()
    def test_invalid_history_and_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab,h=self.make(tmp)
            with self.assertRaises(ValueError):h.history(0)
            with self.assertRaises(ValueError):HypothesisEngine(lab,minimum_per_arm=0)
            lab.close()
