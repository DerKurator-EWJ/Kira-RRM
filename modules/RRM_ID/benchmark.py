"""Reproducible synthetic benchmark; not representative of Android/Kotlin."""
import random, time, statistics
from rrm_id import *

def run(n=100000, seed=42):
    rng = random.Random(seed)
    widths = [1,3,7,13,37,64,73,137]
    records = [Record(KIND_NODE, INLINE, rng.getrandbits(b), b) for b in (rng.choices(widths, weights=[10,20,30,20,10,5,3,2], k=n))]
    start = time.perf_counter(); hybrid = b''.join(map(encode, records)); encode_s = time.perf_counter()-start
    start = time.perf_counter(); pos=0; checksum=0
    while pos<len(hybrid):
        rec,pos=decode(hybrid,pos); checksum ^= rec.value
    decode_s=time.perf_counter()-start
    # 64-bit-only baseline stores values >64 bits in 2 or 3 slots; does not include type/length metadata.
    fixed_bytes=sum(8*((r.bits+63)//64 or 1) for r in records)
    print(f'n={n}, hybrid_bytes={len(hybrid)}, fixed_64bit_payload_only_bytes={fixed_bytes}')
    print(f'hybrid/fixed={len(hybrid)/fixed_bytes:.3f}; encode_s={encode_s:.3f}; decode_s={decode_s:.3f}; checksum={checksum}')
    print('CAVEAT: fixed baseline excludes metadata; timing is hybrid Python only, not a speed comparison.')

if __name__=='__main__': run()
