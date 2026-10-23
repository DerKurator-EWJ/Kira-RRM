import argparse, math, json
from pathlib import Path
from foundation.audio import wav_frames
from foundation.pipeline import AudioPipeline

def synthetic(frames, size):
    # Deterministic two-tone test, with phase reset per frame.
    for i in range(frames):
        frequency=220 if (i//8)%2==0 else 440
        yield tuple(int(11000*math.sin(2*math.pi*frequency*j/16000)) for j in range(size))

def main():
    parser=argparse.ArgumentParser(description='KIRA FOUNDATION v0.6 integrated audio pipeline')
    parser.add_argument('--wav',type=Path)
    parser.add_argument('--frames',type=int,default=80)
    parser.add_argument('--size',type=int,default=1024)
    parser.add_argument('--stream',default='audio:demo')
    parser.add_argument('--db',type=Path,default=Path('data/pipeline.sqlite'))
    parser.add_argument('--codebook',type=Path,default=Path('data/pipeline_codebook.json'))
    parser.add_argument('--min-occurrences',type=int,default=3)
    args=parser.parse_args()
    if args.frames<1 or args.size<2 or args.min_occurrences<2:
        parser.error('frames >=1, size >=2, min-occurrences >=2 required')
    source=wav_frames(args.wav,args.size) if args.wav else synthetic(args.frames,args.size)
    pipe=AudioPipeline(args.db,args.codebook,args.stream,args.size)
    try:
        def limited():
            for i,frame in enumerate(source):
                if i>=args.frames:break
                yield frame
        ingest=pipe.ingest(limited())
        report=pipe.analyze(min_occurrences=args.min_occurrences)
        print('KIRA FOUNDATION v0.6 / INTEGRATED PIPELINE')
        print(json.dumps({'ingest':ingest,'analysis':report},indent=2,ensure_ascii=False))
        print('DB:',args.db,'CODEBOOK:',args.codebook)
    finally:
        pipe.close()
if __name__=='__main__':main()
