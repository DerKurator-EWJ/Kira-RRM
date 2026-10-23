import tempfile,unittest
from pathlib import Path
from foundation.ids import stable_id,compare
from foundation.store import Store
class FoundationTests(unittest.TestCase):
    def test_determinism(self):self.assertEqual(stable_id('node','x'),stable_id('node','x'))
    def test_namespace(self):self.assertNotEqual(stable_id('node','x'),stable_id('relation','x'))
    def test_schemes_differ(self):self.assertFalse(compare('node','fraggle')['equal'])
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'store.db';s=Store(path);s.relate('A','bewegt','B');s.close();s=Store(path)
            self.assertEqual(s.outgoing('A'),[('bewegt','B')]);s.close()
    def test_scheme_separation(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'store.db');s.relate('A','kennt','B','runtime')
            self.assertEqual(s.outgoing('A','forge'),[]);self.assertEqual(s.outgoing('A','runtime'),[('kennt','B')]);s.close()
if __name__=='__main__':unittest.main()
