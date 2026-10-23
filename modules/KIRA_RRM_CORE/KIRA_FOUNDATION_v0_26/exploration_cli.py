"""Kira v0.9 controlled causal exploration shell."""
import argparse,json
from foundation.exploration import ExplorationLab

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/exploration.sqlite');p.add_argument('--seed',type=int,default=7)
    args=p.parse_args();lab=ExplorationLab(args.db,args.seed)
    print('KIRA FOUNDATION v0.9 | Experimentierlabor | help fuer Befehle')
    try:
        while True:
            try:parts=input('KIRA EXP > ').strip().split()
            except (EOFError,KeyboardInterrupt):break
            if not parts:continue
            try:
                cmd=parts[0].lower()
                if cmd=='help':print('observe [N] | do A|B 0|1 [N] | explore [N] | choose | report | history [N] | exit')
                elif cmd=='observe':lab.observe(int(parts[1]) if len(parts)>1 else 1);print('Beobachtungen gespeichert')
                elif cmd=='do':
                    if len(parts)<3:raise ValueError('do A|B 0|1 [N]')
                    rows=lab.intervene(parts[1].upper(),int(parts[2]),int(parts[3]) if len(parts)>3 else 1)
                    print('Experimente:',len(rows),'letztes:',rows[-1] if rows else None)
                elif cmd=='explore':
                    rows=lab.explore(int(parts[1]) if len(parts)>1 else 1)
                    print('Automatisch gewaehlt:',len(rows),'letztes:',rows[-1] if rows else None)
                elif cmd=='choose':print('Naechste Intervention:',lab.choose())
                elif cmd=='report':print(json.dumps(lab.report(),indent=2))
                elif cmd=='history':print(json.dumps(lab.recent(int(parts[1]) if len(parts)>1 else 5),indent=2))
                elif cmd in ('exit','stop','quit'):break
                else:print('Unbekannter Befehl; help')
            except (ValueError,IndexError) as e:print('ERROR:',e)
    finally:lab.close()
if __name__=='__main__':main()
