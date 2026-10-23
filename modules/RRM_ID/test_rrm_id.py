import unittest
from rrm_id import *

class Tests(unittest.TestCase):
    def test_odd_lengths(self):
        for bits in (0,1,3,7,13,37,64,73,137):
            r = Record(KIND_NODE, INLINE, (1 << bits)-1, bits)
            wire = encode(r)
            self.assertEqual(decode(wire), (r,len(wire)))
    def test_all_modes(self):
        for r in (Record(KIND_NODE, INLINE, 5,3), Record(KIND_STATE,REFERENCE,999,13), Record(KIND_RELATION,COMPOSITE,refs=(0,17,20000))):
            self.assertEqual(decode(encode(r))[0],r)
    def test_arena_and_process_identity(self):
        a = Arena()
        x = a.put(Record(KIND_NODE,INLINE,1,1))
        y = a.put(Record(KIND_NODE,INLINE,0,1))
        self.assertEqual(a.put(Record(KIND_NODE,INLINE,1,1)),x)
        relation = a.relation(x,y,x)
        self.assertEqual(a.get(relation).refs,(x,y,x))
        p = ProcessTable(a); pid = p.start(x); p.advance(pid,y)
        self.assertEqual(pid,0); self.assertEqual(p.current[pid],y)
    def test_reject_truncated(self):
        with self.assertRaises(ValueError): decode(bytes([7,73]))
    def test_reject_padding(self):
        with self.assertRaises(ValueError): decode(bytes([4,255,255]))
    def test_reject_noncanonical(self):
        with self.assertRaises(ValueError): decode(bytes([7,13,0,0]))
    def test_concatenation(self):
        a=encode(Record(KIND_NODE,INLINE,3,3)); b=encode(Record(KIND_NODE,INLINE,7,7))
        x,pos=decode(a+b); y,end=decode(a+b,pos)
        self.assertEqual((x.value,y.value,end),(3,7,len(a+b)))

if __name__ == '__main__': unittest.main()
