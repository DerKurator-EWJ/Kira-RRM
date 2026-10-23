"""Interactive v0.8 shell; type help for commands."""
import argparse,json,math
from pathlib import Path
from foundation.live import LiveRuntime
from foundation.audio import wav_frames

def demo_frames(n,size,start=0):
    for i in range(start,start+n):
        freq=220 if (i//8)%2==0 else 440
        yield tuple(int(11000*math.sin(2*math.pi*freq*j/16000)) for j in range(size))

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,default=Path('data/live.sqlite'))
    p.add_argument('--stream',default='audio:live');p.add_argument('--size',type=int,default=1024)
    a=p.parse_args();runtime=LiveRuntime(a.db,a.stream,a.size)
    print('KIRA FOUNDATION v0.8 | help for commands | starts PAUSED')
    try:
        while True:
            try:cmd=input('KIRA > ').strip().split()
            except (EOFError,KeyboardInterrupt):print();break
            if not cmd:continue
            try:
                name=cmd[0].lower()
                if name=='help':print('start/resume | pause | step [N] | wav PATH [N] | status | macros [MIN] | history [N] | predict | predictions [N] | stop/exit')
                elif name in ('start','resume'):runtime.resume();print('RUNNING (commands drive processing; no background audio capture)')
                elif name=='pause':runtime.pause();print('PAUSED')
                elif name=='step':
                    n=int(cmd[1]) if len(cmd)>1 else 1
                    if not 0<=n<=100000:raise ValueError('N must be 0..100000')
                    start=runtime.tick
                    print('Processed:',runtime.run(demo_frames(n,a.size,start)))
                elif name=='wav':
                    if len(cmd)<2:raise ValueError('wav PATH [N]')
                    n=int(cmd[2]) if len(cmd)>2 else 100
                    if not 0<=n<=100000:raise ValueError('N must be 0..100000')
                    print('Processed:',runtime.run(wav_frames(cmd[1],a.size),n))
                elif name=='status':print(json.dumps(runtime.status(),indent=2))
                elif name=='macros':print(json.dumps(runtime.candidates(int(cmd[1]) if len(cmd)>1 else 3),indent=2))
                elif name=='history':print(json.dumps(runtime.history(int(cmd[1]) if len(cmd)>1 else 10),indent=2))
                elif name=='predict':print(json.dumps(runtime.predict(),indent=2))
                elif name=='predictions':print(json.dumps(runtime.prediction_history(int(cmd[1]) if len(cmd)>1 else 10),indent=2))
                elif name in ('stop','exit','quit'):break
                else:print('Unknown command; type help')
            except (ValueError,RuntimeError,OSError) as e:print('ERROR:',e)
    finally:runtime.close()
if __name__=='__main__':main()
