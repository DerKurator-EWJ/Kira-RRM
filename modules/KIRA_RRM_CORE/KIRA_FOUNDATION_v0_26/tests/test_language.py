import unittest
from pathlib import Path
from foundation.language import run,ident,h63
ROOT=Path(__file__).resolve().parents[1]
class LanguageTests(unittest.TestCase):
    def test_fabric(self):
        r=run((ROOT/'examples/fabric.eqx').read_text());self.assertEqual(r['mode'],'FABRIC');self.assertEqual(len(r['triples']),5);self.assertEqual(r['ticks'],2)
        self.assertEqual(r['triples'][0],(ident('entity','doozers'),ident('relation','bauen'),ident('entity','bauwerke')))
    def test_tree(self):
        r=run((ROOT/'examples/tree.eqx').read_text());self.assertEqual(r['mode'],'TREE');self.assertEqual(r['tree'].state,'SEALED');self.assertEqual(len(r['tree'].nodes),5)
    def test_forest(self):
        r=run((ROOT/'examples/forest.eqx').read_text());self.assertEqual(r['mode'],'FOREST');self.assertEqual(len(r['forest'].history),1);self.assertIsInstance(r['forest'].macro,int)
    def test_deterministic(self):
        src=(ROOT/'examples/fabric.eqx').read_text();self.assertEqual(run(src)['triples'],run(src)['triples'])
    def test_validation(self):
        with self.assertRaises(ValueError):run('FABRIC f CELLS 1\nWORK x a b c UNKNOWN ctx NEXT\nRUN')
    def test_no_implicit_run(self):
        self.assertEqual(run('FABRIC f CELLS 1\nWORK x a b c RELATE ctx NEXT')['triples'],[])
if __name__=='__main__':unittest.main()
