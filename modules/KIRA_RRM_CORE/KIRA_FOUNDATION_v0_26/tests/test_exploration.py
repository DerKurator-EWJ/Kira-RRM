import tempfile,unittest
from pathlib import Path
from foundation.exploration import ExplorationLab,ToyWorld

class ExplorationTests(unittest.TestCase):
    def test_deterministic_world_and_intervention(self):
        w=ToyWorld(3)
        self.assertEqual(w.sample(5),w.sample(5))
        obs,_=w.sample(5,('A',0));self.assertEqual(obs['A'],0)
        with self.assertRaises(ValueError):w.sample(1,('X',1))
    def test_balanced_autonomous_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            l=ExplorationLab(str(Path(tmp)/'x.sqlite'))
            self.assertEqual(l.choose(),('A',0))
            l.explore(40)
            r=l.report();self.assertEqual(r['interventions'],40)
            self.assertEqual([r['variables'][t]['arms'][v]['interventional']['n'] for t in ('A','B') for v in (0,1)],[10]*4)
            l.close()
    def test_persistence_and_seed_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'x.sqlite')
            l=ExplorationLab(path,4);l.observe(8);l.explore(8);l.close()
            l=ExplorationLab(path,4);self.assertEqual(l.report()['observations'],8);self.assertEqual(l.report()['interventions'],8);l.close()
            with self.assertRaises(ValueError):ExplorationLab(path,5)
    def test_confounding_vs_causal_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            l=ExplorationLab(str(Path(tmp)/'x.sqlite'))
            l.observe(3000);l.explore(4000)
            r=l.report()['variables']
            self.assertGreater(r['A']['association_difference'],0.15)
            self.assertLess(abs(r['A']['intervention_difference']),0.12)
            self.assertGreater(r['B']['intervention_difference'],0.30)
            l.close()
    def test_validation_and_isolated_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            l=ExplorationLab(str(Path(tmp)/'x.sqlite'))
            with self.assertRaises(ValueError):l.observe(-1)
            with self.assertRaises(ValueError):l.intervene('C',1)
            self.assertIsNone(l.report()['variables']['A']['intervention_difference'])
            l.close()
