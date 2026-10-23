from foundation.compression import ResearchState
from pathlib import Path

path=Path('data/kira_research.sqlite')
s=ResearchState(str(path))
stream='demo:macro:v04'
if not s.events(stream):
    for t in ([1,2,3,9,1,2,3,8,1,2,3,7,1,2,3,6,1,2,3,5]*5):
        s.observe(t,stream)
raw=s.events(stream)
print('KIRA FOUNDATION v0.4 | Persistente Makros & verlustfreie Kompression')
print('Datenbank:',path,'| Ereignisse:',len(raw))
print('Kandidaten:',len(s.candidate_counts(stream)))
metrics=s.consolidate(stream,min_occurrences=3,max_width=6,max_levels=3)
for k,v in metrics.items():print(f'{k}: {v}')
assert s.restore(stream)==raw
print('Roundtrip OK; Speicherung OK')
s.close()
