import tempfile
import unittest
from pathlib import Path
from foundation.generalization import RelationGraph
from foundation.hierarchical_structures import reconstruct,canonical_edges
from foundation.macro_routing import MacroRouter,bucket,mapping_for


def graph(edges):
    return RelationGraph(sorted({n for a,_,b in edges for n in (a,b)}),edges)

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.temp.name)/'routing.sqlite')
        self.a=[(1,'PRECEDES',2),(2,'PRECEDES',3),(3,'PRECEDES',1)]
        self.b=[(91,'PRECEDES',82),(82,'PRECEDES',73),(73,'PRECEDES',91)]
    def tearDown(self):self.temp.cleanup()
    def test_id_invariant_bucket(self):self.assertEqual(bucket(self.a),bucket(self.b))
    def test_exact_mapping(self):self.assertIsNotNone(mapping_for(self.a,self.b))
    def test_direction_mismatch(self):
        self.assertIsNone(mapping_for([(1,'x',2),(2,'x',3)],[(4,'x',5),(6,'x',5)]))
    def test_label_mismatch(self):
        self.assertIsNone(mapping_for(self.a,[(91,'PRECEDES',82),(82,'OTHER',73),(73,'PRECEDES',91)]))
    def test_template_reuse(self):
        r=MacroRouter(self.path)
        try:
            first=r.learn('a',graph(self.a));second=r.learn('b',graph(self.b))
            self.assertFalse(first['cache_hit']);self.assertTrue(second['cache_hit'])
            self.assertEqual(first['template_id'],second['template_id'])
            self.assertEqual(canonical_edges(self.b),reconstruct(second['tree']))
            self.assertEqual(r.stats()['templates'],1)
        finally:r.close()
    def test_persistent_restart(self):
        r=MacroRouter(self.path);r.learn('a',graph(self.a));r.close()
        r=MacroRouter(self.path)
        try:self.assertTrue(r.learn('b',graph(self.b))['cache_hit'])
        finally:r.close()
    def test_no_false_hit(self):
        r=MacroRouter(self.path)
        try:
            r.learn('a',graph(self.a))
            out=r.learn('c',graph([(1,'PRECEDES',2),(2,'PRECEDES',3)]))
            self.assertFalse(out['cache_hit']);self.assertEqual(r.stats()['templates'],2)
        finally:r.close()
    def test_roundtrip_persisted(self):
        r=MacroRouter(self.path)
        try:
            out=r.learn('b',graph(self.b))
            self.assertEqual(reconstruct(r.load(out['run_id'])),canonical_edges(self.b))
        finally:r.close()
    def test_stream_validation(self):
        r=MacroRouter(self.path)
        try:
            with self.assertRaises(ValueError):r.learn('',graph(self.a))
        finally:r.close()
