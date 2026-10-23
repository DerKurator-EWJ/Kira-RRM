"""Bounded partial directed, typed graph analogy. No causal validation."""
import itertools
from .generalization import MAX_NODES


def partial_matches(source, target, min_edges=2, min_precision=0.5, limit=10):
    """Return best edge-supported injective correspondences, or ambiguity.

    Compare mapped source edges with induced target edges. Score = matched /
    union; missing and extra edges both penalize. Nodes outside map are ignored.
    All maximum-score ties are counted (up to 7! mappings); `limit` affects
    returned examples only, not ambiguity detection.
    """
    if not isinstance(min_edges,int) or min_edges<1: raise ValueError('min_edges must be positive integer')
    if not 0 < min_precision <= 1: raise ValueError('min_precision must be in (0,1]')
    if not isinstance(limit,int) or limit<1: raise ValueError('limit must be positive')
    s_nodes=sorted(source.nodes,key=repr); t_nodes=sorted(target.nodes,key=repr)
    best=None; winners=[]; total=0
    # All injective maps of subsets, capped by RelationGraph.MAX_NODES.
    for k in range(2,min(len(s_nodes),len(t_nodes))+1):
        for s_subset in itertools.combinations(s_nodes,k):
            for t_perm in itertools.permutations(t_nodes,k):
                mapping=dict(zip(s_subset,t_perm))
                projected={(mapping[a],r,mapping[b]) for a,r,b in source.edges if a in mapping and b in mapping}
                induced={(a,r,b) for a,r,b in target.edges if a in t_perm and b in t_perm}
                common=projected & induced
                if len(common)<min_edges: continue
                union=projected | induced
                precision=len(common)/len(union)
                if precision+1e-12<min_precision:continue
                # Prioritize number of supported edges, then structural agreement,
                # then node coverage. This avoids tiny perfect motifs dominating.
                rank=(len(common),precision,k)
                if best is None or rank>best:
                    best=rank; winners=[];total=0
                if rank==best:
                    total+=1
                    if len(winners)<limit:
                        missing=sorted(projected-common,key=repr)
                        extra=sorted(induced-common,key=repr)
                        winners.append({'mapping':mapping,'matched_edges':len(common),'agreement':round(precision,6),
                                        'source_only':missing,'target_only':extra,
                                        'supported_edges':sorted(common,key=repr)})
    if best is None:return {'status':'NO_PARTIAL_MATCH','ambiguity_count':0,'matches':[]}
    return {'status':'UNIQUE_PARTIAL_MATCH' if total==1 else 'AMBIGUOUS_PARTIAL_MATCH',
            'ambiguity_count':total,'matches':winners,'score':{'matched_edges':best[0],'agreement':round(best[1],6),'mapped_nodes':best[2]}}


def partial_transfer(source,target,proposals,**kwargs):
    """Only map source-supported proposals on a unique map.

    Missing target edges are flagged as hypotheses, already-present edges as
    analogies; neither is a causal confirmation. Ambiguous maps transfer none.
    """
    for a,b,label in proposals:
        if (a,label,b) not in source.edges:raise ValueError('proposal not supported by source graph')
    result=partial_matches(source,target,**kwargs)
    result['proposals']=[]
    if result['status']!='UNIQUE_PARTIAL_MATCH':return result
    mapping=result['matches'][0]['mapping']
    for a,b,label in proposals:
        if a not in mapping or b not in mapping:continue
        projected=(mapping[a],label,mapping[b])
        result['proposals'].append({'source':mapping[a],'target':mapping[b],'relation':label,
            'status':'OBSERVED_ANALOGY_UNVERIFIED' if projected in target.edges else 'MISSING_EDGE_HYPOTHESIS_UNVERIFIED'})
    return result
