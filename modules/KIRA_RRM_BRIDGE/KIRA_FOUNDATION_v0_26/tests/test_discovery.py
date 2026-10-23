import tempfile,unittest
from pathlib import Path
from foundation.exploration import ExplorationLab
from foundation.discovery import DiscoveryEngine

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'test.sqlite')
        self.lab=ExplorationLab(self.path);self.engine=DiscoveryEngine(self.lab)
    def tearDown(self):self.lab.close();self.tmp.cleanup()
    def test_no_hardcoded_candidates(self):
        self.assertEqual(self.engine.candidates(),[])
        self.assertEqual(self.engine.choose(),None)
        self.assertEqual(self.engine.explore(10),[])
    def test_discover_from_observations(self):
        self.lab.observe(3000)
        found=self.engine.scan()
        self.assertIn('A',found)
        self.assertIn('B',found)
        self.assertEqual(len(self.engine.candidates()),2)
    def test_intervention_distinguishes_spurious(self):
        self.lab.observe(3000);self.engine.scan();self.engine.explore(4000)
        result={r['variable']:r for r in self.engine.review()}
        self.assertEqual(result['A']['status'],'SUPPORTED_NEGLIGIBLE_EFFECT')
        self.assertEqual(result['B']['status'],'SUPPORTED_POSITIVE_EFFECT')
    def test_restart_persists_candidates(self):
        self.lab.observe(3000);self.engine.scan();before=self.engine.candidates()
        self.lab.close();self.lab=ExplorationLab(self.path);self.engine=DiscoveryEngine(self.lab)
        self.assertEqual(self.engine.candidates(),before)
    def test_scans_idempotently(self):
        self.lab.observe(3000);self.engine.scan();self.engine.scan()
        self.assertEqual(len(self.engine.candidates()),2)
    def test_insufficient_data(self):
        self.lab.observe(10);self.assertEqual(self.engine.scan(),[])
    def test_review_history(self):
        self.lab.observe(3000);self.engine.scan();self.engine.review()
        self.assertEqual(len(self.engine.history()),2)
