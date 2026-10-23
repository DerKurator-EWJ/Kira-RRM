"""RRM-KERN 0.1: finite relational event traces and open, resumable inquiry.
Proof-of-concept; not a general intelligence or complete RRM semantics.
"""
import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

class Kern:
    def __init__(self, path='kern.sqlite', depth=6):
        self.db = sqlite3.connect(path)
        self.depth = depth
        self.db.execute('CREATE TABLE IF NOT EXISTS events (stream TEXT NOT NULL, pos INTEGER NOT NULL, token TEXT NOT NULL, PRIMARY KEY(stream,pos))')
        self.db.execute('CREATE TABLE IF NOT EXISTS predictions (stream TEXT NOT NULL, pos INTEGER NOT NULL, predicted TEXT, actual TEXT NOT NULL, PRIMARY KEY(stream,pos))')
        self.db.commit()

    def events(self, stream):
        return [r[0] for r in self.db.execute('SELECT token FROM events WHERE stream=? ORDER BY pos', (stream,))]

    def predict(self, stream, prefix=None):
        # Only predict from earlier transitions; a repeated prefix is not a guarantee.
        history = self.events(stream)
        prefix = history if prefix is None else list(prefix)
        for n in range(min(self.depth, len(prefix)), 0, -1):
            ctx = prefix[-n:]
            choices = Counter(history[i+n] for i in range(len(history)-n) if history[i:i+n] == ctx)
            if choices:
                ordered = sorted(choices.items(), key=lambda kv: (-kv[1], kv[0]))
                return {'state':'HYPOTHESIS', 'next':ordered[0][0], 'depth':n, 'support':sum(choices.values()), 'alternatives':ordered, 'certainty':ordered[0][1]/sum(choices.values())}
        return {'state':'OPEN', 'question':'Welche Fortsetzung folgt auf diesen Kontext?', 'context':prefix[-self.depth:]}

    def observe(self, stream, tokens):
        before = self.events(stream)
        reports = []
        with self.db:
            for token in tokens:
                token = str(token)
                result = self.predict(stream, before)
                pos = len(before)
                self.db.execute('INSERT INTO events VALUES (?,?,?)', (stream,pos,token))
                self.db.execute('INSERT INTO predictions VALUES (?,?,?,?)', (stream,pos,result.get('next'),token))
                reports.append({'position':pos, 'observed':token, 'prediction':result.get('next'), 'matched':result.get('next') == token if 'next' in result else None})
                before.append(token)
        return reports

    def dream(self, stream, steps):
        # Hypothetical continuation only; NEVER added to observed history.
        context = self.events(stream)
        output=[]
        for _ in range(steps):
            guess=self.predict(stream,context)
            if guess['state']=='OPEN': break
            output.append(guess['next'])
            context.append(guess['next'])
        return {'generated':output,'status':'HYPOTHETICAL','stopped_early':len(output)<steps}

    def audit(self, stream):
        rows=list(self.db.execute('SELECT predicted,actual FROM predictions WHERE stream=?',(stream,)))
        judged=[(a,b) for a,b in rows if a is not None]
        return {'observations':len(rows),'judged':len(judged),'correct':sum(a==b for a,b in judged), 'accuracy':sum(a==b for a,b in judged)/len(judged) if judged else None}

def main():
    p=argparse.ArgumentParser(description='RRM-KERN 0.1 / relational sequence experiment')
    p.add_argument('--db',default='kern.sqlite');p.add_argument('--stream',default='default')
    sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('observe');q.add_argument('tokens',nargs='+')
    sub.add_parser('predict')
    q=sub.add_parser('dream');q.add_argument('--steps',type=int,default=8)
    sub.add_parser('audit');sub.add_parser('history')
    args=p.parse_args();k=Kern(args.db)
    if args.cmd=='observe': result=k.observe(args.stream,args.tokens)
    elif args.cmd=='predict':result=k.predict(args.stream)
    elif args.cmd=='dream':result=k.dream(args.stream,max(0,args.steps))
    elif args.cmd=='audit':result=k.audit(args.stream)
    else:result=k.events(args.stream)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
