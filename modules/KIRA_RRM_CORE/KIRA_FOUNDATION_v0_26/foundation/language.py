"""Faithful, testable Python port of EquinoxMindCore.kt (v0.3-android).
Original Kotlin remains under reference/runtime/. No claim of independent cognition.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib, shlex
from .ids import stable_id

ISA={'RELATE','SPLIT','MIRROR','UNIFY','DISSONATE','HOLD','WAKE','SEAL','EMIT'}
CONT={'NEXT','HOLD_INFINITY','SEAL'}
def h63(person, raw):
    v=int.from_bytes(hashlib.blake2b(raw.encode(),digest_size=8,person=person.encode('ascii')).digest(),'big') & ((1<<63)-1)
    return v or 1

def ident(ns,s):return stable_id(ns,s,'runtime')
def kt_list(xs):return '['+', '.join(map(str,xs))+']'
def kt_triple(t):return f'SymbolicTriple(subject={t[0]}, relation={t[1]}, objectValue={t[2]})'

def lines(src):
    for i,raw in enumerate(src.splitlines(),1):
        line=raw.split('#',1)[0].strip()
        if line:
            try: yield i,shlex.split(line)
            except ValueError as e: raise ValueError(f'line {i}: {e}') from e

@dataclass
class Node:
    node_id:str
    role:str
    triples:set=field(default_factory=set)
    parent:str|None=None
    state:str='ACTIVE'
    thesis:list=field(default_factory=list)
    anti:list=field(default_factory=list)
    synthesis:str|None=None
    dissonance:str|None=None

class Tree:
    def __init__(self,name):
        self.name=name;self.nodes={'root':Node('root','TRUNK')};self.state='ACTIVE';self.version=0;self.macro=None
    def branch(self,parent,side,triple,name):
        if parent not in self.nodes:raise ValueError('unknown parent '+parent)
        if side not in ('THESIS','ANTITHESIS'):raise ValueError('invalid side')
        triples=sorted(set([triple]));raw=parent+'|'+side+'|'+name+''.join('|'+('/'.join(t)) for t in triples)
        prefix='t' if side=='THESIS' else 'a';base=f'{prefix}_{h63("EQXNODE1",raw):x}';nid=base;n=1
        while nid in self.nodes:nid=f'{base}_{n}';n+=1
        self.nodes[nid]=Node(nid,side,set(triples),parent)
        (self.nodes[parent].thesis if side=='THESIS' else self.nodes[parent].anti).append(nid)
        self.version+=1;self.macro=None;return nid
    def mirror(self,parent):
        if parent not in self.nodes:raise ValueError('unknown parent '+parent)
        p=self.nodes[parent];left=set().union(*(self.nodes[x].triples for x in p.thesis)) if p.thesis else set();right=set().union(*(self.nodes[x].triples for x in p.anti)) if p.anti else set()
        if not left or not right:raise ValueError('mirror requires thesis and antithesis')
        exact=left&right;frames=sorted({(s,r) for s,r,o in left}&{(s,r) for s,r,o in right})
        pairs=[(a,b) for frame in frames for a in left for b in right if a[:2]==frame and b[:2]==frame and a!=b]
        # Kotlin Set iteration order follows insertion; for deterministic equivalent use sorted inputs.
        synth_raw='S|'+parent+'|'+kt_list([f'({s}, {r})' for s,r in frames])+'|'+kt_list([kt_triple(x) for x in sorted(exact)])
        diss_raw='D|'+parent+'|'+', '.join(kt_triple(a)+'>'+kt_triple(b) for a,b in pairs)
        sid=f's_{h63("EQXNODE1",synth_raw):x}';did=f'd_{h63("EQXNODE1",diss_raw):x}'
        self.nodes[sid]=Node(sid,'SYNTHESIS',exact|{(s,r,'*') for s,r in frames},parent)
        self.nodes[did]=Node(did,'DISSONANCE',left^right,parent)
        p.synthesis=sid;p.dissonance=did;self.version+=1;self.macro=None
        return len(frames),len(pairs)
    def wake(self,node):
        if node not in self.nodes or self.nodes[node].state=='EXTINCT':raise ValueError('unknown or extinct node '+node)
        self.nodes[node].state='ACTIVE';self.state='ACTIVE'
    def seal(self):
        for n in self.nodes.values():
            if n.state=='ACTIVE':n.state='SEALED' if n.thesis or n.anti or n.synthesis or n.dissonance else 'HOLD_INFINITY'
        self.state='SEALED';self.macro=h63('EQXTREE1',self.structural());return self.macro
    def structural(self):
        out=self.name+'|root'
        for n in sorted(self.nodes.values(),key=lambda x:x.node_id):
            out+='|'+n.node_id+':'+n.role+':'+(n.parent or '-')
            for t in sorted(n.triples):out+=':'+('/'.join(t))
            out+=':'+','.join(sorted(n.thesis))+':'+','.join(sorted(n.anti))+':'+(n.synthesis or '-')+':'+(n.dissonance or '-')
        return out
    def extinct(self):
        self.state='EXTINCT'
        for n in self.nodes.values():n.state='EXTINCT'

def tree_triples(t):
    out=set();tree_id=ident('tree',f'{t.name}:{t.macro or 0}')
    for n in t.nodes.values():
        nid=ident('node',f'{t.name}:{n.node_id}')
        out|={(tree_id,ident('relation','has_node'),nid),(nid,ident('relation','role'),ident('role',n.role.lower())),(nid,ident('relation','state'),ident('state',n.state.lower()))}
        if n.parent:out.add((nid,ident('relation','parent'),ident('node',f'{t.name}:{n.parent}')))
        for i,(s,r,o) in enumerate(sorted(n.triples)):
            fid=ident('fact',f'{t.name}:{n.node_id}:{i}:{s}:{r}:{o}')
            out|={(nid,ident('relation','asserts'),fid),(fid,ident('relation','subject'),ident('concept',s)),(fid,ident('relation','relation'),ident('relation',r)),(fid,ident('relation','object'),ident('concept',o))}
    return sorted(out)

def run_tree(src):
    t=None;mirrors=0
    for lineno,p in lines(src):
        op=p[0].upper()
        try:
            if op=='TREE' and len(p)==2 and t is None:t=Tree(p[1])
            elif op in ('THESIS','ANTITHESIS') and len(p)==6 and t:t.branch(p[2],op,tuple(p[3:]),p[1])
            elif op=='MIRROR' and len(p)==2 and t:t.mirror(p[1]);mirrors+=1
            elif op=='SEAL' and len(p)==1 and t:t.seal()
            elif op=='WAKE' and len(p)==2 and t:t.wake(p[1])
            elif op=='EXTINCT' and len(p)==1 and t:t.extinct()
            else:raise ValueError('invalid TREE command '+op)
        except Exception as e:raise ValueError(f'line {lineno}: {e}') from e
    if t is None:raise ValueError('no TREE')
    return {'mode':'TREE','summary':f'TREE {t.name} | nodes {len(t.nodes)} | mirror {mirrors} | state {t.state} | macro {t.macro or "open"}','triples':tree_triples(t),'tree':t}

def fabric_execute(p):
    s,r,c,op,ctx=p['subject'],p['relation'],p['counterpart'],p['operation'],p['context']
    def derived(channel):return h63('EQXOUT03',f'[{s},{r},{c},{ctx},"{channel}"]')
    kr=lambda x:ident('kernel_relation',x)
    if op in ('RELATE','EMIT'):return [(s,r,c)]
    if op=='SPLIT':return [(s,kr('thesis'),derived('thesis')),(s,kr('antithesis'),derived('antithesis'))]
    if op=='MIRROR':return [(ctx,kr('synthesis'),derived('synthesis')),(ctx,kr('dissonance'),derived('dissonance'))]
    if op in ('UNIFY','DISSONATE'):
        x='synthesis' if op=='UNIFY' else 'dissonance';return [(ctx,kr(x),derived(x))]
    return [(s,kr('state'),ident('kernel_state',{'WAKE':'active','SEAL':'sealed','HOLD':'hold_infinity'}[op]))]

def run_fabric(src):
    name=None;cells=0;queue=[];outputs=[];ticks=0;identities={};counts=[];packets=0
    def identity(ns,s):
        value=ident(ns,s);identities[f'{ns}:{s}']=value;return value
    for lineno,p in lines(src):
        op=p[0].upper()
        try:
            if op=='FABRIC' and len(p)==4 and p[2].upper()=='CELLS' and name is None:
                name=p[1];cells=int(p[3]);assert cells>=1;counts=[0]*cells
            elif op=='WORK' and len(p)>=8 and name is not None:
                _,label,s,r,c,operation,ctx,cont,*payload=p;operation=operation.upper();cont=cont.upper()
                if operation not in ISA or cont not in CONT:raise ValueError('invalid operation or continuation')
                si=identity('entity',s);ri=identity('relation',r);ci=identity('entity',c);oi=identity('operation',operation);ct=identity('context',ctx);co=identity('continuation',cont);pi=[identity('payload',x) for x in payload]
                raw=f'{{"context":{ct},"continuation":{co},"counterpart":{ci},"operation":{oi},"payload":{kt_list(pi).replace(" ","")},"relation":{ri},"subject":{si}}}'
                packet=h63('EQXPACK3',raw);identities['packet:'+label]=packet
                queue.append({'packet':packet,'subject':si,'relation':ri,'counterpart':ci,'operation':operation,'context':ct});packets+=1
            elif op=='RUN' and len(p)==1 and name is not None:
                while queue:
                    for cell in range(cells):
                        if not queue:break
                        outputs.extend(fabric_execute(queue.pop(0)));counts[cell]+=1
                    ticks+=1
            else:raise ValueError('invalid FABRIC command '+op)
        except Exception as e:raise ValueError(f'line {lineno}: {e}') from e
    if name is None:raise ValueError('no FABRIC')
    return {'mode':'FABRIC','summary':f'FABRIC {name} | cells {cells} | packets {packets} | ticks {ticks} | outputs {len(outputs)}','triples':outputs,'identities':identities,'ticks':ticks,'counts':counts}

class Forest:
    def __init__(self,name):self.name=name;self.trees={};self.links=[];self.queue=[];self.history=[];self.macro=None
    def relate(self,a,an,r,b,bn,bidir=True):
        if a not in self.trees or b not in self.trees:raise ValueError('unknown tree')
        lid=h63('EQXLINK02',f'{a}|{an}|{r}|{b}|{bn}|{str(bidir).lower()}');self.links.append((lid,a,an,r,b,bn,bidir));self.macro=None
    def delta(self,tree,node,reason):
        for _,a,an,r,b,bn,bi in self.links:
            if a==tree and (an==node or an=='*' or node=='*'):self.queue.append((tree,b,bn,r,reason))
            if bi and b==tree and (bn==node or bn=='*' or node=='*'):self.queue.append((tree,a,an,r,reason))
    def run(self):
        while self.queue:
            item=self.queue.pop(0);_,b,bn,_,_=item;t=self.trees.get(b)
            if t:t.wake(bn if bn in t.nodes and bn!='*' else 'root');self.history.append(item)
    def seal(self):
        if not all(t.state=='SEALED' for t in self.trees.values()):raise ValueError('all trees must be sealed')
        raw=self.name+''.join('|'+name+'='+str(t.macro if t.macro is not None else t.seal()) for name,t in sorted(self.trees.items()))+''.join('|'+str(x[0]) for x in sorted(self.links))
        self.macro=h63('EQXFORE2',raw);return self.macro

def run_forest(src):
    src_lines=src.splitlines();i=0;f=None
    while i<len(src_lines):
        lineno=i+1;line=src_lines[i].split('#',1)[0].strip();i+=1
        if not line:continue
        try:
            p=shlex.split(line);op=p[0].upper()
            if op=='FOREST' and len(p)==2 and f is None:f=Forest(p[1])
            elif op=='BEGIN_TREE' and len(p)==2 and f:
                body=['TREE '+p[1]];found=False
                while i<len(src_lines):
                    row=src_lines[i];i+=1
                    if row.split('#',1)[0].strip().upper()=='END_TREE':found=True;break
                    body.append(row)
                if not found:raise ValueError('missing END_TREE')
                t=run_tree('\n'.join(body))['tree']
                if t.state!='SEALED':raise ValueError('tree must be sealed')
                f.trees[t.name]=t
            elif op=='RELATE' and len(p) in (6,7) and f:f.relate(p[1],p[2],p[3],p[4],p[5],len(p)==6 or p[6].upper()!='ONEWAY')
            elif op=='EXTERNAL' and len(p) in (3,4) and f:f.delta(p[1],p[2],p[3] if len(p)==4 else 'external')
            elif op=='REFINE' and len(p)==8 and f:
                t=f.trees[p[1]];side=p[3].upper()
                if side not in ('THESIS','ANTITHESIS'):raise ValueError('invalid side')
                t.wake(p[2]);t.branch(p[2],side,tuple(p[5:8]),p[4]);f.delta(p[1],p[2],'refine')
            elif op=='RUN' and len(p)==1 and f:f.run()
            elif op=='SETTLE' and len(p)==2 and f:f.trees[p[1]].seal()
            elif op=='SETTLE_ALL' and len(p)==1 and f:
                for t in f.trees.values():t.seal()
            elif op=='SEAL_FOREST' and len(p)==1 and f:f.seal()
            else:raise ValueError('invalid FOREST command '+op)
        except Exception as e:raise ValueError(f'line {lineno}: {e}') from e
    if f is None:raise ValueError('no FOREST')
    triples=set()
    for t in f.trees.values():triples.update(tree_triples(t))
    for _,a,an,r,b,bn,bi in f.links:triples.add((ident('tree',a),ident('relation','forest_relation'),ident('tree',b)))
    return {'mode':'FOREST','summary':f'FOREST {f.name} | trees {len(f.trees)} | links {len(f.links)} | wakes {len(f.history)} | macro {f.macro or "open"}','triples':sorted(triples),'forest':f}

def run(src):
    first=next(lines(src),None)
    if first is None:raise ValueError('empty program')
    mode=first[1][0].upper()
    return {'TREE':run_tree,'FABRIC':run_fabric,'FOREST':run_forest}[mode](src)
