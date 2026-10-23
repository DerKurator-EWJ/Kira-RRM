"""RRM 0.3: conservative, evidence-backed single-edge transformation induction.
No causal claims. Rules are hypotheses, not observations.
"""
import json
from collections import Counter
from itertools import permutations, product


def _mapping(source, target):
    """Find unique structural node alignment based on unchanged edge identities.
    Return (mapping, removed edge, added edge) only for one unambiguous relabel.
    """
    sn, tn = source['nodes'], target['nodes']
    if len(sn) != len(tn) or len(sn) > 7 or Counter(sn.values()) != Counter(tn.values()):
        return None
    groups = [[n for n in sn if sn[n] == label] for label in sorted(set(sn.values()))]
    targets = [[n for n in tn if tn[n] == label] for label in sorted(set(sn.values()))]
    candidates = set()
    old = Counter(tuple(e) for e in source['edges'])
    new = Counter(tuple(e) for e in target['edges'])
    for combo in product(*(permutations(g) for g in targets)):
        mapping = dict(zip((n for g in groups for n in g), (n for g in combo for n in g)))
        mapped = Counter((mapping[a], r, mapping[b]) for (a, r, b), count in old.items() for _ in range(count))
        removed = list((mapped - new).elements())
        added = list((new - mapped).elements())
        if len(removed) == len(added) == 1:
            a, oldrel, b = removed[0]
            x, newrel, y = added[0]
            if a == x and b == y and oldrel != newrel:
                # Record only rule identity, not arbitrary node IDs.
                candidates.add((tn[a], oldrel, tn[b], newrel))
    return next(iter(candidates)) if len(candidates) == 1 else None


def induce(source, target):
    """Infer a candidate typed relation relabeling from an observed state pair."""
    return _mapping(source, target)


def apply(state, rule):
    """Transfer to a novel graph only if exactly one edge matches.
    Reject ambiguous matches; preserve every other edge and node.
    """
    src_type, oldrel, dst_type, newrel = rule
    matches = [i for i, (a, rel, b) in enumerate(state['edges'])
               if rel == oldrel and state['nodes'][a] == src_type and state['nodes'][b] == dst_type]
    if len(matches) != 1:
        return None
    result = json.loads(json.dumps(state))
    result['edges'][matches[0]][1] = newrel
    return result
