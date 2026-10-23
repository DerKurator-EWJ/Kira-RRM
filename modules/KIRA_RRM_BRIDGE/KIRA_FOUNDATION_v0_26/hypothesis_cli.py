"""Kira v0.10 persistent hypothesis laboratory."""
import argparse,json
from foundation.exploration import ExplorationLab
from foundation.hypotheses import HypothesisEngine

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/hypotheses.sqlite');p.add_argument('--seed',type=int,default=7)
    args=p.parse_args();lab=ExplorationLab(args.db,args.seed);engine=HypothesisEngine(lab)
    print('KIRA FOUNDATION v0.10 | Hypothesenlabor | help fuer Befehle')
    try:
        while True:
            try:parts=input('KIRA HYP > ').strip().split()
            except (EOFError,KeyboardInterrupt):break
            if not parts:continue
            try:
                cmd=parts[0].lower()
                if cmd=='help':print('observe [N] | explore [N] | do A|B 0|1 [N] | hypotheses | review | choose | history [N] | report | exit')
                elif cmd=='observe':lab.observe(int(parts[1]) if len(parts)>1 else 1);print('Beobachtungen gespeichert')
                elif cmd=='explore':
                    rows=engine.explore(int(parts[1]) if len(parts)>1 else 1)
                    print('Experimente:',len(rows),'letztes:',rows[-1] if rows else None)
                elif cmd=='do':
                    if len(parts)<3:raise ValueError('do A|B 0|1 [N]')
                    rows=lab.intervene(parts[1].upper(),int(parts[2]),int(parts[3]) if len(parts)>3 else 1)
                    print('Experimente:',len(rows))
                elif cmd=='hypotheses':print(json.dumps([engine.evaluate(t) for t in ('A','B')],indent=2))
                elif cmd=='review':print(json.dumps(engine.review(),indent=2))
                elif cmd=='choose':print('Naechstes Experiment:',engine.choose())
                elif cmd=='history':print(json.dumps(engine.history(int(parts[1]) if len(parts)>1 else 10),indent=2))
                elif cmd=='report':print(json.dumps(lab.report(),indent=2))
                elif cmd in ('exit','quit','stop'):break
                else:print('Unbekannter Befehl; help')
            except (ValueError,IndexError) as e:print('ERROR:',e)
    finally:lab.close()
if __name__=='__main__':main()
