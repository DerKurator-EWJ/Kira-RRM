"""Microbenchmark: direct record-handle DIFF vs materialized Python-state DIFF.
Includes SQLite record reads for binary path; does not include state ingestion.
"""
from time import perf_counter
from runtime import BinaryRuntime
from binary_ops import BinaryOps
from rrm05 import changes

def make(rel):
    return {'nodes':{'a':'point','b':'point','c':'signal'},'edges':[['a',rel,'b'],['c','red','a']]}

rt=BinaryRuntime(); ops=BinaryOps(rt)
a=make('near'); b=make('far'); ah=rt.store_state(a); bh=rt.store_state(b)
N=3000
for label,fn in [('binary_diff',lambda:ops.diff(ah,bh)),('materialize_and_diff',lambda:changes(rt.load_state(ah),rt.load_state(bh))),('in_memory_python_diff',lambda:changes(a,b))]:
    start=perf_counter()
    for _ in range(N): fn()
    print(f'{label}: {(perf_counter()-start)*1000:.2f} ms / {N} operations')
rt.close()
