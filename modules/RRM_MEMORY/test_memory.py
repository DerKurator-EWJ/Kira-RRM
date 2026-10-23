import tempfile, unittest
from pathlib import Path
from memory import RAMStore, DiskStore, RoutedCacheStore, make_db

class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'records.db'
        self.rows=[(i,bytes([(i%3)<<5])+bytes([i%256])*(i%11+1)) for i in range(90)]
        make_db(self.path,self.rows)
    def tearDown(self): self.temp.cleanup()
    def test_identical_records(self):
        a=RAMStore(self.rows); b=DiskStore(self.path); c=RoutedCacheStore(self.path,32)
        for i,_ in self.rows:
            self.assertEqual(a.get(i),b.get(i)); self.assertEqual(a.get(i),c.get(i))
        b.close(); c.close()
    def test_route(self):
        a=RAMStore(self.rows); b=DiskStore(self.path); c=RoutedCacheStore(self.path,32)
        for family in range(3):
            self.assertEqual(a.route(family),b.route(family)); self.assertEqual(a.route(family),c.route(family))
        b.close(); c.close()
    def test_cache_limit(self):
        c=RoutedCacheStore(self.path,32)
        for i in range(90): c.get(i)
        self.assertLessEqual(c.peak_bytes,32)
        c.get(89); self.assertGreater(c.hits,0)
        c.close()
    def test_missing_handle(self):
        for store in (RAMStore(self.rows),DiskStore(self.path),RoutedCacheStore(self.path,32)):
            with self.assertRaises(KeyError): store.get(1000)
            if hasattr(store,'close'):store.close()

if __name__=='__main__': unittest.main()
