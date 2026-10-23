from pathlib import Path
from foundation.generalization import RelationGraph
from foundation.partial_macro_routing import PartialMacroRouter,benchmark,verify_plan

def graph(edges):
    return RelationGraph(sorted({v for a,_,b in edges for v in (a,b)}),edges)

def main():
    p=Path('data/partial_router.sqlite');r=PartialMacroRouter(p)
    try:
        known=graph([(1,'PRECEDES',2),(2,'PRECEDES',3)])
        new=graph([(91,'PRECEDES',82),(82,'PRECEDES',73),(73,'PRECEDES',64)])
        r.register(known)
        run,plan=r.learn('world:new',new)
        print('KIRA FOUNDATION v0.18 | PARTIAL ROUTING')
        print('run:',run,'reused edges:',plan['reused_edge_count'],'fresh edges:',plan['fresh_edge_count'])
        print('reconstructed:',verify_plan(r.load(run)))
        print('benchmark (different workloads):',benchmark(new,r.templates(),repeats=20))
        print('sqlite:',p)
    finally:r.close()
if __name__=='__main__':main()
