"""Experimental bounded online macro discovery, inspired by Runtime/Forge.
NOT a direct port of their complete learning or persistence algorithms.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib

@dataclass(frozen=True)
class Macro:
    macro_id: int
    tokens: tuple[int, ...]
    occurrences: int
    estimated_net_savings: int

class OnlineMacroLearner:
    def __init__(self, min_size=2, max_size=6, min_occurrences=3, definition_overhead=1):
        if not (2 <= min_size <= max_size and min_occurrences >= 2):
            raise ValueError('invalid macro policy')
        self.min_size=min_size;self.max_size=max_size
        self.min_occurrences=min_occurrences;self.definition_overhead=definition_overhead
        self.counts=Counter();self.streams=defaultdict(list)
    def observe(self, token, modality='generic', source_level=0):
        if not isinstance(token,int) or isinstance(token,bool):raise TypeError('token must be an integer ID')
        key=(modality,source_level);tail=self.streams[key];tail.append(token)
        for n in range(self.min_size,min(self.max_size,len(tail))+1):
            self.counts[(key,tuple(tail[-n:]))]+=1
    def candidates(self, modality='generic', source_level=0):
        key=(modality,source_level);out=[]
        for (stream,tokens),freq in self.counts.items():
            if stream!=key or freq<self.min_occurrences:continue
            # optimistic proxy, not an exact encoding or non-overlapping compression measurement
            saving=(len(tokens)-1)*freq-(len(tokens)+self.definition_overhead)
            if saving<=0:continue
            payload=(str(key)+'|'+','.join(map(str,tokens))).encode()
            macro_id=int.from_bytes(hashlib.blake2b(payload,digest_size=8,person=b'KIRAMAC3').digest(),'big')&((1<<63)-1)
            out.append(Macro(macro_id,tokens,freq,saving))
        return sorted(out,key=lambda x:(-x.estimated_net_savings,-len(x.tokens),x.tokens))

class HierarchicalRouteIndex:
    """Python adaptation of Runtime two-token anchor / eligible-span exact matching."""
    def __init__(self):self.routes=defaultdict(lambda:defaultdict(lambda:defaultdict(dict)))
    def register(self,macro,modality='generic',source_level=0):
        tokens=tuple(macro.tokens)
        if len(tokens)<2:raise ValueError('macro must contain >=2 tokens')
        self.routes[(modality,source_level)][tokens[-2:]][len(tokens)][tokens]=macro.macro_id
    def probe(self,current,modality='generic',source_level=0,max_allowed_span=None):
        current=tuple(current)
        if len(current)<2:return None,0
        bucket=self.routes.get((modality,source_level),{}).get(current[-2:],{})
        limit=len(current) if max_allowed_span is None else min(len(current),max_allowed_span)
        eligible=sorted((n for n in bucket if n<=limit),reverse=True)
        checked=0
        for n in eligible:
            checked+=1
            mid=bucket[n].get(current[-n:])
            if mid is not None:return (mid,n),checked
        return None,checked

def exhaustive_probe(index,current,modality='generic',source_level=0,max_allowed_span=None):
    """Reference full span enumeration; count exact signature lookups."""
    current=tuple(current);limit=len(current) if max_allowed_span is None else min(len(current),max_allowed_span)
    bucket=index.routes.get((modality,source_level),{});checked=0
    for n in range(limit,1,-1):
        checked+=1
        match=bucket.get(current[-2:],{}).get(n,{}).get(current[-n:])
        if match is not None:return (match,n),checked
    return None,checked
