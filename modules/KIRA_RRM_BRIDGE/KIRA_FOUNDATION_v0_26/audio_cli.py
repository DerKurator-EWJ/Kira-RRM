import argparse, math, time, tracemalloc, wave, struct
from pathlib import Path
from foundation.audio import AdaptiveAudio,wav_frames,fft_magnitudes

def synthetic(count,size):
    for i in range(count):
        f=220 if (i//8)%2==0 else 440
        yield tuple(int(11000*math.sin(2*math.pi*f*j/16000)) for j in range(size))

def main():
    ap=argparse.ArgumentParser(description='KIRA audio ID experiment')
    ap.add_argument('--wav',type=Path);ap.add_argument('--frames',type=int,default=48)
    ap.add_argument('--size',type=int,default=1024);ap.add_argument('--codebook',type=Path,default=Path('data/audio_codebook.json'))
    ap.add_argument('--benchmark',action='store_true');args=ap.parse_args()
    if args.size<=0 or args.size&(args.size-1):ap.error('--size must be a positive power of two')
    frames=list(wav_frames(args.wav,args.size) if args.wav else synthetic(args.frames,args.size))[:args.frames]
    if not frames:raise SystemExit('No full frames available')
    q=AdaptiveAudio.load(args.codebook)
    t=time.perf_counter(); ids=[q.quantize(f)['id'] for f in frames];dt=time.perf_counter()-t
    q.save(args.codebook)
    print('KIRA FOUNDATION v0.5 / AUDIO')
    print('frames:',len(frames),'IDs:',len(set(ids)),'prototypes:',len(q.prototypes))
    print('new:',q.created,'reused:',q.reused,'audio seconds per frame (mean):',round(dt/len(frames),6))
    print('first IDs:',ids[:16]);print('codebook:',args.codebook)
    if args.benchmark:
        tracemalloc.start();t=time.perf_counter()
        for f in frames:fft_magnitudes(f)
        fft_time=time.perf_counter()-t;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        print('pure Python radix-2 FFT total seconds:',round(fft_time,4),'peak traced bytes:',peak)
        print('Audio path is feature extraction + adaptive matching; FFT path is full spectrum only.')
        print('TIMES ARE NOT EQUIVALENT TASKS OR OPTIMIZED FFT COMPARISONS.')
if __name__=='__main__':main()
