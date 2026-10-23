from pathlib import Path
from foundation.generalization import RelationGraph, GeneralizationStore
from foundation.partial_generalization import partial_transfer

def main():
    a=RelationGraph([101,102,103,104],[(101,'activates',102),(102,'activates',103),(102,'inhibits',104)])
    b=RelationGraph([901,888,777,666,555],[(901,'activates',888),(888,'activates',777),(888,'activates',666),(555,'observes',901)])
    result=partial_transfer(a,b,[(102,104,'inhibits')],min_edges=2,min_precision=.5)
    print('KIRA FOUNDATION v0.13 | Partielle Struktur-Analogie')
    print('Status:',result['status'],'| Gleichwertige Zuordnungen:',result['ambiguity_count'])
    print('Score:',result.get('score'))
    print('Beste Zuordnungen:',result['matches'][:2])
    print('Transfer (nur bei eindeutiger Zuordnung):',result['proposals'])
    store=GeneralizationStore(Path(__file__).parent/'data'/'partial.sqlite')
    try:print('Gespeicherter Versuch:',store.record(a,b,result))
    finally:store.close()
if __name__=='__main__':main()
