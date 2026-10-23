import argparse
import json
from foundation.event_graph import EventGraphLab

def main():
    p=argparse.ArgumentParser(description='Kira v0.14: temporal event graph discovery')
    p.add_argument('--db',default='data/event_graph.sqlite')
    p.add_argument('--live-db',help='Import v0.7+ live.sqlite events')
    p.add_argument('--live-stream',default='audio:live')
    a=p.parse_args()
    lab=EventGraphLab(a.db)
    try:
        if a.live_db:
            n=lab.import_live(a.live_db,a.live_stream)
            print('Newly imported events:',n)
            print(json.dumps(lab.snapshot(a.live_stream),indent=2))
        else:
            lab.ingest('world:a',[1,2,3,1,2,3,1,2,3,1,2,3])
            lab.ingest('world:b',[91,82,73,91,82,73,91,82,73,91,82,73])
            print('World A:',json.dumps(lab.snapshot('world:a'),indent=2))
            print('World B:',json.dumps(lab.snapshot('world:b'),indent=2))
            print('Analogy:',json.dumps(lab.compare('world:a','world:b'),indent=2))
    finally:lab.close()
if __name__=='__main__':main()
