import tempfile
import unittest
from pathlib import Path
from foundation.epistemic_regulation import EpistemicCore

class EpistemicTests(unittest.TestCase):
    def test_empty(self):
        c=EpistemicCore(); self.assertIsNone(c.model("A")); c.close()
    def test_consolidate(self):
        c=EpistemicCore(); [c.observe("A","B") for _ in range(3)]; self.assertEqual(c.model("A")["prediction"],"B"); c.close()
    def test_single_contradiction_no_revision(self):
        c=EpistemicCore(); [c.observe("A","B") for _ in range(5)]; c.observe("A","C"); self.assertEqual(c.model("A")["prediction"],"B"); c.close()
    def test_revision(self):
        c=EpistemicCore(budget=100); [c.observe("A","B") for _ in range(5)]; [c.observe("A","C") for _ in range(10)]; self.assertEqual(c.model("A")["prediction"],"C"); self.assertEqual(len(c.history("A")),1); c.close()
    def test_history(self):
        c=EpistemicCore(budget=100); [c.observe("A","B") for _ in range(5)]; [c.observe("A","C") for _ in range(10)]; self.assertEqual(c.history("A")[0]["old"],"B"); c.close()
    def test_budget(self):
        c=EpistemicCore(budget=1); [c.observe("A","B") for _ in range(3)]; self.assertEqual(c.observe("A","C")["action"],"defer_budget"); c.close()
    def test_reset_budget(self):
        c=EpistemicCore(budget=1); [c.observe("A","B") for _ in range(3)]; c.reset_budget(); self.assertEqual(c.observe("A","C")["action"],"investigate"); c.close()
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/"e.db"); c=EpistemicCore(path); [c.observe("A","B") for _ in range(3)]; c.close(); c=EpistemicCore(path); self.assertEqual(c.model("A")["prediction"],"B"); c.close()
    def test_independent_contexts(self):
        c=EpistemicCore(); [c.observe("A","B") for _ in range(3)]; [c.observe("X","Y") for _ in range(3)]; self.assertEqual(c.model("X")["prediction"],"Y"); c.close()
    def test_bad_input(self):
        c=EpistemicCore();
        with self.assertRaises(ValueError): c.observe("", "B")
        c.close()
    def test_invalid_budget(self):
        with self.assertRaises(ValueError): EpistemicCore(budget=0)
