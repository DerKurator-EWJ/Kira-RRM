import unittest
import tempfile
from pathlib import Path
from foundation.compression import HierarchicalCompressor,ResearchState

class TestCompression(unittest.TestCase):
 def test_roundtrip_and_real_savings(self):
  raw=[1,2,3,4]*40
  c=HierarchicalCompressor(max_levels=3)
  encoded=c.compress(raw)
  self.assertEqual(c.expand(encoded),raw)
  self.assertGreater(c.metrics(raw,encoded)['net_saved_token_slots'],0)
 def test_no_false_savings(self):
  raw=list(range(100))
  c=HierarchicalCompressor();enc=c.compress(raw)
  self.assertEqual(enc,raw)
  self.assertEqual(c.rules,[])
 def test_recursive_rules(self):
  raw=([1,2,3,4]*3+[99])*30
  c=HierarchicalCompressor(max_levels=3)
  enc=c.compress(raw)
  self.assertEqual(c.expand(enc),raw)
  self.assertTrue(any(any(t<0 for t in r.expansion) for r in c.rules))
 def test_negative_input_ids(self):
  raw=[-1,-2,-1,-2]*20
  c=HierarchicalCompressor();enc=c.compress(raw)
  self.assertEqual(c.expand(enc),raw)
 def test_persistence_and_isolation(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(Path(d)/'state.sqlite')
   s=ResearchState(p)
   for t in [7,8]*20:s.observe(t,'audio')
   for t in [3,4]*10:s.observe(t,'video')
   self.assertEqual(s.candidate_counts('audio')[(7,8)],20)
   metrics=s.consolidate('audio')
   self.assertGreater(metrics['net_saved_token_slots'],0)
   s.close()
   s=ResearchState(p)
   self.assertEqual(s.restore('audio'),[7,8]*20)
   self.assertEqual(s.events('video'),[3,4]*10)
   s.close()
 def test_invalid(self):
  with self.assertRaises(TypeError):HierarchicalCompressor().compress([True])
  with self.assertRaises(ValueError):HierarchicalCompressor(max_levels=0)
if __name__=='__main__':unittest.main()
