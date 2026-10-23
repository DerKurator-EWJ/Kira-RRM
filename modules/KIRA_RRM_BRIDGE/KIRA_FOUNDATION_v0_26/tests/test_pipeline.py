import math, tempfile, unittest
from pathlib import Path
from foundation.pipeline import AudioPipeline
from foundation.compression import ResearchState

def tone(f=220,n=1024):
    return tuple(int(11000*math.sin(2*math.pi*f*j/16000)) for j in range(n))

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'state.sqlite'
        self.codebook=Path(self.tmp.name)/'codebook.json'
    def tearDown(self):self.tmp.cleanup()
    def test_full_pipeline_roundtrip(self):
        p=AudioPipeline(self.db,self.codebook,'audio:test')
        p.ingest([tone(220)]*16+[tone(440)]*16)
        result=p.analyze()
        self.assertEqual(result['events'],32)
        self.assertTrue(result['id_roundtrip_ok'])
        self.assertGreater(result['compression']['rules'],0)
        p.close()
    def test_restart_keeps_events_and_codebook(self):
        p=AudioPipeline(self.db,self.codebook,'audio:test')
        p.ingest([tone()]*8)
        first=p.store.events('audio:test');protos=len(p.quantizer.prototypes)
        p.close()
        p=AudioPipeline(self.db,self.codebook,'audio:test')
        p.ingest([tone()]*8)
        self.assertEqual(p.store.events('audio:test'),first+first)
        self.assertEqual(len(p.quantizer.prototypes),protos)
        self.assertTrue(p.analyze()['id_roundtrip_ok'])
        p.close()
    def test_separate_streams(self):
        a=AudioPipeline(self.db,self.codebook,'audio:a');a.ingest([tone()]*4);a.close()
        b=AudioPipeline(self.db,self.codebook,'audio:b');b.ingest([tone(440)]*5)
        self.assertEqual(len(b.store.events('audio:a')),4)
        self.assertEqual(len(b.store.events('audio:b')),5)
        b.close()
    def test_invalid_frame_does_not_append(self):
        p=AudioPipeline(self.db,self.codebook,'audio:test')
        with self.assertRaises(ValueError):p.ingest([(1,2,3)])
        self.assertEqual(p.store.events('audio:test'),[])
        p.close()
    def test_empty_analysis(self):
        p=AudioPipeline(self.db,self.codebook,'audio:test')
        result=p.analyze()
        self.assertEqual(result['events'],0)
        self.assertTrue(result['id_roundtrip_ok'])
        p.close()
