import json, os, random, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'RRM_RUNTIME_0_2'))
from rrm_id import Record, KIND_NODE, KIND_RELATION, KIND_STATE, INLINE, encode, decode
from memory import RAMStore, DiskStore, RoutedCacheStore, make_db


def build_rows(n=12000):
    rng = random.Random(812)
    kinds = (KIND_NODE, KIND_RELATION, KIND_STATE)
    rows=[]
    for i in range(n):
        bits = rng.choice((3, 7, 13, 37, 64, 73, 137))
        value = rng.getrandbits(bits)
        rows.append((i, encode(Record(kinds[i%3], INLINE, value, bits))))
    return rows


def measure(store, keys, family=KIND_RELATION):
    t0=time.perf_counter()
    checksum=0
    for key in keys:
        payload=store.get(key)
        rec, end=decode(payload)
        assert end == len(payload)
        checksum = (checksum + rec.value + rec.kind) & ((1<<64)-1)
    elapsed=time.perf_counter()-t0
    t1=time.perf_counter()
    selected=store.route(family)
    route_elapsed=time.perf_counter()-t1
    return dict(seconds=round(elapsed,6), route_seconds=round(route_elapsed,6), checksum=checksum,
                routed=len(selected), loads=store.loads, bytes_loaded=store.bytes_loaded,
                cache_hits=getattr(store,'hits',0), cache_peak_payload_bytes=getattr(store,'peak_bytes',0))


def run(n=12000, lookups=10000, cache_bytes=65536):
    rows=build_rows(n)
    rng=random.Random(113)
    hot=[rng.randrange(min(128,n)) if rng.random()<0.9 else rng.randrange(n) for _ in range(lookups)]
    uniform=[rng.randrange(n) for _ in range(lookups)]
    results={'parameters': {'records':n, 'lookups_per_pattern':lookups, 'cache_budget_payload_bytes':cache_bytes}}
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'records.sqlite'
        make_db(path,rows)
        results['sqlite_file_bytes']=os.stat(path).st_size
        results['wire_payload_bytes']=sum(len(v) for _,v in rows)
        for pattern, keys in (('hot90',hot),('uniform',uniform)):
            results[pattern]={}
            for label, store in (('ram',RAMStore(rows)),('disk',DiskStore(path)),('routed_cache',RoutedCacheStore(path,cache_bytes))):
                try:
                    results[pattern][label]=measure(store,keys)
                finally:
                    if hasattr(store,'close'): store.close()
            checks={r['checksum'] for r in results[pattern].values()}
            assert len(checks)==1, 'backends returned different values'
    return results

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
