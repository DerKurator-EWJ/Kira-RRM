import unittest
from foundation.macros import OnlineMacroLearner,HierarchicalRouteIndex,exhaustive_probe
class TestMacros(unittest.TestCase):
 def test_repetition(self):
  l=OnlineMacroLearner(min_occurrences=3)
  for x in [1,2,3,4]*5:l.observe(x)
  self.assertIn((1,2,3),[m.tokens for m in l.candidates()])
 def test_stream_isolation(self):
  l=OnlineMacroLearner(min_occurrences=2)
  for x in [1,2]*4:l.observe(x,modality='audio')
  self.assertEqual(l.candidates(modality='video'),[])
 def test_longest_match(self):
  l=OnlineMacroLearner(min_occurrences=3)
  for x in [1,2,3,4]*5:l.observe(x)
  idx=HierarchicalRouteIndex()
  for m in l.candidates():idx.register(m)
  self.assertEqual(idx.probe([7,1,2,3,4])[0],exhaustive_probe(idx,[7,1,2,3,4])[0])
 def test_unknown(self):
  idx=HierarchicalRouteIndex()
  self.assertEqual(idx.probe([99,100]),(None,0))
 def test_stability(self):
  def go():
   l=OnlineMacroLearner(min_occurrences=2)
   for x in [4,5,4,5,4,5]:l.observe(x)
   return [(m.macro_id,m.tokens) for m in l.candidates()]
  self.assertEqual(go(),go())
 def test_invalid(self):
  with self.assertRaises(ValueError):OnlineMacroLearner(min_size=1)
  with self.assertRaises(TypeError):OnlineMacroLearner().observe('abc')
if __name__=='__main__':unittest.main()
