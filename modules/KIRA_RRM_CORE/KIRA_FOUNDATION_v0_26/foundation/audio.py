"""Experimental Python port of the time-domain feature and adaptive codebook logic.
Based on reference/runtime/AdaptiveAudioQuantizer.kt. Not yet Kotlin parity certified.
"""
import math, json, wave, struct
from pathlib import Path
from dataclasses import dataclass
LAGS=(4,8,16,32,64,128,256,512)
WEIGHTS=(1.,1.,.75,1.15,.65,.65)
SILENCE_ID=-1000001

def features(frame):
    if not frame: return (0.,)*6,0.,True
    xs=[float(x)/32768. for x in frame]
    rms=math.sqrt(sum(x*x for x in xs)/len(xs))
    if rms<.0025: return (0.,)*6,rms,True
    n=len(xs); zc=sum((xs[i]>=0)!=(xs[i-1]>=0) for i in range(1,n))
    zcr_raw=zc/max(1,n-1)
    hz=max(40.,min(18000.,zcr_raw*24000.))
    zcr=max(0.,min(1.,math.log(hz/40.)/math.log(18000./40.)))
    rough=min(1.,sum(abs(xs[i]-xs[i-1]) for i in range(1,n))/max(1,n-1)/max(rms,1e-9)/2.8)
    best=-1.; best_i=0
    for k,lag in enumerate(LAGS):
        if lag>=n: continue
        xy=sum(frame[i]*frame[i-lag] for i in range(lag,n))
        xx=sum(frame[i]*frame[i] for i in range(lag,n))
        yy=sum(frame[i-lag]*frame[i-lag] for i in range(lag,n))
        corr=min(1.,abs(xy/math.sqrt(max(1.,xx*yy))))
        if corr>best: best=corr; best_i=k
    quarter=max(1,n//4)
    env=[]
    for q in range(4):
        a=q*quarter;b=n if q==3 else min(n,a+quarter)
        env.append(sum(abs(x) for x in xs[a:b])/max(1,b-a))
    slope=max(-1.,min(1.,((env[2]+env[3]-env[0]-env[1])*.5)/max(rms,1e-9)))
    pulse=min(1.,(max(env)-min(env))/max(rms*1.5,1e-9))
    return (zcr,rough,best_i/7.,max(0.,best),(.5*(slope+1)),pulse),rms,False

@dataclass
class Prototype:
    id:int
    center:list
    count:int=1
    radius_ema:float=.015

class AdaptiveAudio:
    def __init__(self):
        self.prototypes=[];self.next_ordinal=1;self.accepted=0;self.created=0;self.reused=0
        self.learned_structure_count=0
    @staticmethod
    def distance(a,b):
        return min(1.,math.sqrt(sum(w*(x-y)**2 for x,y,w in zip(a,b,WEIGHTS))/sum(WEIGHTS)))
    @staticmethod
    def bucket(x):return tuple(min(4,max(0,int(min(1.,max(0.,v))*5.))) for v in x)
    def candidates(self,x):
        coords=self.bucket(x)
        keys={coords}
        for axis in range(6):
            for delta in (-1,1):
                c=list(coords);c[axis]+=delta
                if 0<=c[axis]<=4:keys.add(tuple(c))
        return [p for p in self.prototypes if self.bucket(p.center) in keys]
    @staticmethod
    def familiarity(p):return p.count/(p.count+24.)
    def acceptance_radius(self,p):
        return max(.048,min(.190,.035+.85*p.radius_ema+min(.025,math.log1p(p.count)*.0035)))
    def creation_radius(self,p):
        structural=1-1/(1+math.log1p(max(0,self.learned_structure_count)))
        structural=max(0.,min(.85,structural))
        return max(.024,self.acceptance_radius(p)*(1.08-.34*self.familiarity(p)-.16*structural))
    def quantize(self,frame,learn=True):
        x,rms,silent=features(frame)
        if silent:return {'id':SILENCE_ID,'silent':True,'created':False,'recognized':False,'rms':rms}
        candidates=self.candidates(x)
        p=min(candidates,key=lambda p:self.distance(x,p.center)) if candidates else None
        d=self.distance(x,p.center) if p else 1.
        novel=p is None or d>self.creation_radius(p)
        if not learn:return {'id':p.id if p else SILENCE_ID,'silent':False,'created':False,'recognized':not novel,'rms':rms}
        self.accepted+=1
        if novel:
            p=Prototype(-1000000-self.next_ordinal,list(x));self.next_ordinal+=1
            self.prototypes.append(p);self.created+=1
        else:
            p.count+=1;lr=max(.008,min(.10,1/math.sqrt(p.count+24.)))
            p.center=[v+lr*(target-v) for v,target in zip(p.center,x)]
            p.radius_ema=.95*p.radius_ema+.05*min(1.,d)
            self.reused+=1
        return {'id':p.id,'silent':False,'created':novel,'recognized':True,'rms':rms}
    def save(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        Path(path).write_text(json.dumps({'format':1,'next_ordinal':self.next_ordinal,'accepted':self.accepted,'created':self.created,'reused':self.reused,'prototypes':[vars(p) for p in self.prototypes]},indent=2),encoding='utf8')
    @classmethod
    def load(cls,path):
        obj=cls();path=Path(path)
        if path.exists():
            data=json.loads(path.read_text(encoding='utf8'))
            if data.get('format')!=1:raise ValueError('Unsupported audio codebook format')
            obj.next_ordinal=data['next_ordinal'];obj.accepted=data['accepted'];obj.created=data['created'];obj.reused=data['reused']
            obj.prototypes=[Prototype(**p) for p in data['prototypes']]
        return obj

def wav_frames(path,frame_size=1024):
    with wave.open(str(path),'rb') as w:
        if w.getsampwidth()!=2 or w.getnchannels()!=1 or w.getcomptype()!='NONE':
            raise ValueError('Only uncompressed mono 16-bit PCM WAV supported')
        while True:
            raw=w.readframes(frame_size)
            if len(raw)<frame_size*2:break
            yield struct.unpack('<'+'h'*frame_size,raw)

def fft_magnitudes(frame):
    """Radix-2 FFT reference, pure Python, not an optimized library baseline."""
    n=len(frame)
    if n==0 or n&(n-1):raise ValueError('FFT frame length must be power of two')
    a=[complex(x/32768.,0) for x in frame]
    j=0
    for i in range(1,n):
        bit=n>>1
        while j&bit:j^=bit;bit>>=1
        j^=bit
        if i<j:a[i],a[j]=a[j],a[i]
    length=2
    while length<=n:
        angle=-2*math.pi/length;wlen=complex(math.cos(angle),math.sin(angle))
        for start in range(0,n,length):
            w=1+0j
            for k in range(length//2):
                u=a[start+k];v=a[start+k+length//2]*w
                a[start+k]=u+v;a[start+k+length//2]=u-v;w*=wlen
        length*=2
    return [abs(z) for z in a[:n//2+1]]
