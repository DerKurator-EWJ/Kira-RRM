from foundation.generalization import RelationGraph
from foundation.integrated_routing import IntegratedRouter,benchmark_equal_workload


def graph(edges):
    return RelationGraph(sorted({v for a,_,b in edges for v in (a,b)}),edges)

if __name__=='__main__':
    known=graph([(1,'PRECEDES',2),(2,'PRECEDES',3)])
    novel=graph([(91,'PRECEDES',82),(82,'PRECEDES',73),(73,'PRECEDES',64)])
    lab=IntegratedRouter()
    try:
        lab.register(known)
        run,result=lab.learn('demo',novel,register_new=False)
        print('KIRA FOUNDATION v0.19 | INTEGRATED PARTIAL ROUTING')
        print('run:',run,'reused edges:',result['reused_edges'],'fresh edges:',result['fresh_edges'])
        print('new hierarchy merges:',result['new_merges'])
        print('reconstructed:',result['tree']['original_edges'])
        print('equal-workload benchmark:',benchmark_equal_workload(novel,lab.templates(),50))
    finally:lab.close()
