"""Reproducible two-world structure-transfer experiment."""
from pathlib import Path
from foundation.generalization import RelationGraph, transfer, GeneralizationStore

# Arbitrary, different IDs; same directed topology and relation types.
world_a=RelationGraph([101,102,103,104],[(101,'activates',102),(102,'activates',103),(102,'inhibits',104)])
world_b=RelationGraph([901,888,777,666],[(901,'activates',888),(888,'activates',777),(888,'inhibits',666)])


def main():
    result=transfer(world_a,world_b,[(102,104,'inhibits')])
    db=GeneralizationStore(Path(__file__).parent/'data'/'generalization.sqlite')
    try:
        run_id=db.record(world_a,world_b,result)
        print('KIRA FOUNDATION v0.12 | Strukturelle Generalisierung')
        print('Graph A:',world_a.to_json())
        print('Graph B:',world_b.to_json())
        print('Matching:',result['status'])
        print('Abbildung:',result.get('mapping'))
        print('Uebertragene Hypothesen (UNVERIFIED):',result['proposals'])
        print('Gespeicherter Lauf:',run_id,'| Historie:',len(db.history()))
    finally:db.close()

if __name__=='__main__':main()
