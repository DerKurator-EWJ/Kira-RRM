import argparse,json,tempfile
from pathlib import Path
from foundation.ids import compare
from foundation.store import Store

def main():
    p=argparse.ArgumentParser(description='KIRA FOUNDATION v0.1 — ID compatibility and relational persistence')
    p.add_argument('command',choices=['demo','compare','status']);p.add_argument('--namespace',default='node');p.add_argument('--symbol',default='fraggle');p.add_argument('--db',default='data/kira_foundation.sqlite');a=p.parse_args()
    if a.command=='compare':print(json.dumps(compare(a.namespace,a.symbol),ensure_ascii=False,indent=2));return
    if a.command=='status':print('KIRA FOUNDATION v0.1 | Python stdlib | original sources in reference/ | database:',a.db);return
    print('KIRA FOUNDATION v0.1 | ID- und Relationstest')
    print('ID-Vergleich:',json.dumps(compare('node','fraggle'),ensure_ascii=False))
    store=Store(a.db)
    store.relate('doozers','bauen','konstruktionen')
    store.relate('fraggles','essen','konstruktionen')
    print('Doozers:',store.outgoing('doozers'))
    print('Fraggles:',store.outgoing('fraggles'))
    store.close();print('Persistenz gespeichert:',a.db)
if __name__=='__main__':main()
