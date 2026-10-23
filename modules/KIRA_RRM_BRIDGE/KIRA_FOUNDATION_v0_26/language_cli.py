import argparse,json
from pathlib import Path
from foundation.language import run
from foundation.store import Store

def main():
    parser=argparse.ArgumentParser(description='KIRA FOUNDATION v0.2 | Equinox ID Language')
    parser.add_argument('file',help='Path to .eqx program')
    parser.add_argument('--db',default='data/kira_foundation.sqlite')
    parser.add_argument('--no-save',action='store_true')
    parser.add_argument('--show',type=int,default=12,help='Number of numeric triples to display')
    args=parser.parse_args()
    result=run(Path(args.file).read_text(encoding='utf-8'))
    print('KIRA FOUNDATION v0.2 | '+result['summary'])
    print('Triples:',len(result['triples']))
    for triple in result['triples'][:args.show]:print('  ',*triple)
    if not args.no_save:
        db=Store(args.db)
        try:
            for s,r,o in result['triples']:
                db.db.execute('INSERT OR IGNORE INTO triples(scheme,subject,predicate,object) VALUES(?,?,?,?)',('runtime',s,r,o))
            db.db.commit()
            print('Persistiert in',args.db,'(runtime-ID-Raum, numerische Tripel)')
        finally:db.close()
if __name__=='__main__':main()
