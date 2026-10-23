"""Interactive relational hypothesis discovery laboratory."""
import argparse,json
from foundation.exploration import ExplorationLab
from foundation.discovery import DiscoveryEngine

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/discovery.sqlite');p.add_argument('--seed',type=int,default=7)
    args=p.parse_args();lab=ExplorationLab(args.db,args.seed);engine=DiscoveryEngine(lab)
    print('KIRA FOUNDATION v0.11 | Relationale Hypothesengenerierung | help')
    try:
        while True:
            try:parts=input('KIRA DISC > ').strip().split()
            except (EOFError,KeyboardInterrupt):break
            if not parts:continue
            try:
                cmd=parts[0].lower();n=int(parts[1]) if len(parts)>1 else 1
                if cmd=='help':print('observe [N] | scan | candidates | choose | explore [N] | review | history [N] | report | exit')
                elif cmd=='observe':lab.observe(n);print('Beobachtungen:',n)
                elif cmd=='scan':print('Entdeckte Kandidaten:',engine.scan())
                elif cmd=='candidates':print(json.dumps(engine.candidates(),indent=2))
                elif cmd=='choose':print('Naechste Intervention:',engine.choose())
                elif cmd=='explore':print('Experimente:',len(engine.explore(n)))
                elif cmd=='review':print(json.dumps(engine.review(),indent=2))
                elif cmd=='history':print(json.dumps(engine.history(n if len(parts)>1 else 10),indent=2))
                elif cmd=='report':print(json.dumps(lab.report(),indent=2))
                elif cmd in ('exit','quit','stop'):break
                else:print('Unbekannt; help')
            except (ValueError,IndexError) as e:print('ERROR:',e)
    finally:lab.close()
if __name__=='__main__':main()
