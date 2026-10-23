import argparse
import json
from foundation.event_graph import EventGraphLab
from foundation.structural_macros import StructuralMacroLab


def main():
    p=argparse.ArgumentParser(description='Kira v0.15: reusable structural motifs')
    p.add_argument('--events',default='data/event_graph.sqlite')
    p.add_argument('--macros',default='data/structural_macros.sqlite')
    p.add_argument('--min-count',type=int,default=2)
    p.add_argument('--streams',nargs='+',default=['world:a','world:b'])
    p.add_argument('--live-db',help='Optional live.sqlite import')
    args=p.parse_args()
    events=EventGraphLab(args.events); macros=StructuralMacroLab(args.macros)
    try:
        if args.live_db:
            events.import_live(args.live_db,'audio:live')
            args.streams=['audio:live']+args.streams
        if not args.live_db:
            # Demo streams with the same cycle and unrelated additional observations.
            for stream,sequence in [('world:a',[1,2,3]*8),('world:b',[91,82,73]*8)]:
                events.ingest(stream,sequence)
        for stream in args.streams:
            graph=events.graph(stream,min_count=args.min_count)
            if graph:
                count=macros.learn(stream,graph)
                print(stream,'motifs:',count,'edges:',len(graph.edges))
            else:print(stream,'no graph')
        print('Shared structural macros:')
        print(json.dumps(macros.shared(args.streams),indent=2,ensure_ascii=False))
    finally:
        events.close();macros.close()
if __name__=='__main__':main()
