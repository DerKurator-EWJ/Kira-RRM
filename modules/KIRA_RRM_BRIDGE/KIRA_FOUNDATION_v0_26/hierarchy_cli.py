from foundation.generalization import RelationGraph
from foundation.hierarchical_structures import HierarchyLab,reconstruct

a=RelationGraph([1,2,3],[(1,'PRECEDES',2),(2,'PRECEDES',3),(3,'PRECEDES',1)])
b=RelationGraph([91,82,73],[(91,'PRECEDES',82),(82,'PRECEDES',73),(73,'PRECEDES',91)])
lab=HierarchyLab()
try:
    for name,graph in [('world:a',a),('world:b',b)]:
        run,tree=lab.learn(name,graph)
        print(name,'run',run,'levels',max(n['level'] for n in tree['nodes'].values()),
              'nodes',len(tree['nodes']),'roundtrip edges',len(reconstruct(tree)))
    print('Shared structural IDs:',lab.shared())
    print('Note: structural recurrence is not causal or semantic equivalence.')
finally:lab.close()
