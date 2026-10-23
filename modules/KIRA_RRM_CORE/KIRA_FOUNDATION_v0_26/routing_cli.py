from pathlib import Path
from foundation.generalization import RelationGraph
from foundation.macro_routing import MacroRouter
from foundation.hierarchical_structures import reconstruct

router=MacroRouter()
try:
    for name,graph in [
        ('world:a',RelationGraph([1,2,3],[(1,'PRECEDES',2),(2,'PRECEDES',3),(3,'PRECEDES',1)])),
        ('world:b',RelationGraph([91,82,73],[(91,'PRECEDES',82),(82,'PRECEDES',73),(73,'PRECEDES',91)])),
        ('world:c',RelationGraph([7,8,9],[(7,'PRECEDES',8),(8,'PRECEDES',9)]))]:
        result=router.learn(name,graph)
        print(name,'template',result['template_id'],'cache_hit',result['cache_hit'],
              'candidates',result['candidate_count'],'edges',len(reconstruct(result['tree'])))
    print('Stats:',router.stats())
    print('Routing matches are exact graph isomorphisms, not semantic equivalence.')
finally:router.close()
