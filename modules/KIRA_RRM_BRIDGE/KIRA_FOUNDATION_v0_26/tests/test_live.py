import tempfile,unittest
from pathlib import Path
from foundation.live import LiveRuntime

class LiveTests(unittest.TestCase):
    def test_resume_persist_counts_and_codebook(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'live.sqlite';frame=(1000,-1000)*32
            r=LiveRuntime(path,frame_size=64,max_width=4)
            with self.assertRaises(RuntimeError):r.step(frame)
            r.resume()
            for _ in range(8):r.step(frame)
            self.assertEqual(r.status()['tick'],8)
            self.assertEqual(r.candidates(3)[0]['occurrences'],7)
            self.assertEqual(len(r.history()),8)
            before=r.audio.next_ordinal;r.close()
            r=LiveRuntime(path,frame_size=64,max_width=4)
            self.assertTrue(r.paused)
            self.assertEqual(r.tick,8)
            self.assertEqual(r.audio.next_ordinal,before)
            r.resume();r.step(frame)
            self.assertEqual(r.candidates(3)[0]['occurrences'],8)
            r.close()
    def test_reject_wrong_frame_no_partial_write(self):
        with tempfile.TemporaryDirectory() as td:
            r=LiveRuntime(Path(td)/'a.db',frame_size=8);r.resume()
            with self.assertRaises(ValueError):r.step([1,2])
            self.assertEqual(r.status()['tick'],0)
            r.close()
    def test_stream_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.db'
            for stream in ('one','two'):
                r=LiveRuntime(p,stream,8);r.resume();r.step([100,-100]*4);r.close()
            r=LiveRuntime(p,'one',8);self.assertEqual(r.status()['events'],1);r.close()
    def test_config_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.db';r=LiveRuntime(p,frame_size=8);r.close()
            with self.assertRaises(ValueError):LiveRuntime(p,frame_size=16)

if __name__=='__main__':unittest.main()
