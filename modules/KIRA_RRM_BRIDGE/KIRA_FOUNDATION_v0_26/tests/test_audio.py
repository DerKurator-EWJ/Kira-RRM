import math, tempfile, unittest
from pathlib import Path
from foundation.audio import AdaptiveAudio,features,fft_magnitudes

def sine(hz,n=1024):return [int(11000*math.sin(2*math.pi*hz*i/16000)) for i in range(n)]
class AudioTests(unittest.TestCase):
    def test_silence(self):
        q=AdaptiveAudio();r=q.quantize([0]*1024)
        self.assertTrue(r['silent']);self.assertEqual(len(q.prototypes),0)
    def test_features(self):
        f,r,s=features(sine(220));self.assertEqual(len(f),6);self.assertFalse(s);self.assertTrue(all(0<=v<=1 for v in f))
    def test_reuse(self):
        q=AdaptiveAudio();a=q.quantize(sine(220));b=q.quantize(sine(220))
        self.assertTrue(a['created']);self.assertFalse(b['created']);self.assertEqual(a['id'],b['id'])
    def test_play_no_learning(self):
        q=AdaptiveAudio();q.quantize(sine(220));n=len(q.prototypes)
        self.assertTrue(q.quantize(sine(220),False)['recognized']);self.assertEqual(n,len(q.prototypes))
    def test_persistence(self):
        q=AdaptiveAudio();i=q.quantize(sine(220))['id']
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audio.json';q.save(p);r=AdaptiveAudio.load(p)
            self.assertEqual(i,r.quantize(sine(220),False)['id'])
    def test_fft_peak(self):
        spec=fft_magnitudes(sine(250))
        self.assertEqual(max(range(len(spec)),key=lambda k:spec[k]),16)
    def test_fft_reject_non_power_two(self):
        with self.assertRaises(ValueError):fft_magnitudes([1,2,3])
if __name__=='__main__':unittest.main()
