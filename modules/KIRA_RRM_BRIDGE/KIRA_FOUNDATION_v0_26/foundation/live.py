"""v0.7 research runtime: transactional ticks, persistent online n-gram counts,
checkpointed audio codebook and a replayable event log in one SQLite database.
No autonomous cognition and no background processing while the process is closed.
"""
import json
import sqlite3
from collections import Counter, deque
from pathlib import Path
from .audio import AdaptiveAudio, Prototype
from .prediction import TransitionPredictor

class LiveRuntime:
    def __init__(self, path='data/live.sqlite', stream='audio:live', frame_size=1024, max_width=6):
        if not stream or frame_size < 2 or max_width < 2: raise ValueError('invalid configuration')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db=sqlite3.connect(str(path))
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS live_state(stream TEXT PRIMARY KEY, tick INTEGER NOT NULL, frame_size INTEGER NOT NULL, max_width INTEGER NOT NULL, codebook TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS live_events(stream TEXT NOT NULL, tick INTEGER NOT NULL, token INTEGER NOT NULL, created INTEGER NOT NULL, PRIMARY KEY(stream,tick));
        CREATE TABLE IF NOT EXISTS live_counts(stream TEXT NOT NULL, width INTEGER NOT NULL, signature TEXT NOT NULL, occurrences INTEGER NOT NULL, PRIMARY KEY(stream,width,signature));
        CREATE TABLE IF NOT EXISTS live_log(stream TEXT NOT NULL, tick INTEGER NOT NULL, event TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(stream,tick,event));
        ''')
        self.stream=stream;self.frame_size=frame_size;self.max_width=max_width
        self.predictor=TransitionPredictor(self.db,stream,max_context=3)
        row=self.db.execute('SELECT tick,frame_size,max_width,codebook FROM live_state WHERE stream=?',(stream,)).fetchone()
        if row:
            self.tick,old_size,old_width,raw=row
            if (old_size,old_width)!=(frame_size,max_width):raise ValueError('existing stream configuration differs')
            self.audio=self._decode(raw)
        else:
            self.tick=0;self.audio=AdaptiveAudio()
            with self.db:
                self.db.execute('INSERT INTO live_state VALUES(?,?,?,?,?)',(stream,0,frame_size,max_width,self._encode()))
        tail=self.db.execute('SELECT token FROM live_events WHERE stream=? ORDER BY tick DESC LIMIT ?', (stream,max_width-1)).fetchall()
        self.tail=deque(reversed([x[0] for x in tail]),maxlen=max_width-1)
        recent=self.db.execute('SELECT token FROM live_events WHERE stream=? ORDER BY tick DESC LIMIT ?', (stream,self.predictor.max_context)).fetchall()
        self.prediction_tail=deque(reversed([x[0] for x in recent]),maxlen=self.predictor.max_context)
        self.paused=True

    def _encode(self):
        a=self.audio
        return json.dumps({'format':1,'next_ordinal':a.next_ordinal,'accepted':a.accepted,'created':a.created,'reused':a.reused,'learned_structure_count':a.learned_structure_count,'prototypes':[vars(p) for p in a.prototypes]},separators=(',',':'))
    @staticmethod
    def _decode(raw):
        d=json.loads(raw)
        if d.get('format')!=1:raise ValueError('invalid codebook')
        a=AdaptiveAudio()
        for field in ('next_ordinal','accepted','created','reused','learned_structure_count'):setattr(a,field,d[field])
        a.prototypes=[Prototype(**p) for p in d['prototypes']]
        return a
    def resume(self):self.paused=False
    def pause(self):self.paused=True
    def step(self,frame):
        if self.paused:raise RuntimeError('runtime is paused; use resume')
        if len(frame)!=self.frame_size:raise ValueError('incorrect frame size')
        # Quantizer is restored if the database transaction fails.
        before=self._encode()
        try:
            result=self.audio.quantize(frame)
            next_tick=self.tick+1
            new_tail=list(self.tail)+[result['id']]
            with self.db:
                prediction=self.predictor.record(next_tick,list(self.prediction_tail),result['id'])
                self.db.execute('INSERT INTO live_events VALUES(?,?,?,?)',(self.stream,next_tick,result['id'],int(result['created'])))
                for width in range(2,min(self.max_width,len(new_tail))+1):
                    signature=json.dumps(new_tail[-width:],separators=(',',':'))
                    self.db.execute('''INSERT INTO live_counts VALUES(?,?,?,1) ON CONFLICT(stream,width,signature) DO UPDATE SET occurrences=occurrences+1''',(self.stream,width,signature))
                self.db.execute('INSERT INTO live_log VALUES(?,?,?,?)',(self.stream,next_tick,'observation',json.dumps(result,sort_keys=True)))
                self.db.execute('UPDATE live_state SET tick=?,codebook=? WHERE stream=?',(next_tick,self._encode(),self.stream))
            self.tick=next_tick;self.tail.append(result['id']);self.prediction_tail.append(result['id'])
            return {**result,'prediction':prediction}
        except Exception:
            self.audio=self._decode(before)
            raise
    def run(self,frames,limit=None):
        if limit is not None and limit<0:raise ValueError('negative limit')
        n=0
        for frame in frames:
            if limit is not None and n>=limit:break
            self.step(frame);n+=1
        return n
    def status(self):
        return {'stream':self.stream,'tick':self.tick,'paused':self.paused,'prototypes':len(self.audio.prototypes),
                'macro_signatures':self.db.execute('SELECT COUNT(*) FROM live_counts WHERE stream=?',(self.stream,)).fetchone()[0],
                'events':self.db.execute('SELECT COUNT(*) FROM live_events WHERE stream=?',(self.stream,)).fetchone()[0],
                'prediction':self.predictor.metrics()}
    def candidates(self,min_occurrences=3,limit=10):
        if min_occurrences<1 or limit<1:raise ValueError('invalid candidate query')
        rows=self.db.execute('''SELECT width,signature,occurrences FROM live_counts WHERE stream=? AND occurrences>=? ORDER BY occurrences DESC,width DESC,signature LIMIT ?''',(self.stream,min_occurrences,limit)).fetchall()
        return [{'tokens':json.loads(sig),'occurrences':freq} for _,sig,freq in rows]
    def history(self,limit=10):
        return [{'tick':tick,'event':event,'payload':json.loads(payload)} for tick,event,payload in self.db.execute('SELECT tick,event,payload FROM live_log WHERE stream=? ORDER BY tick DESC LIMIT ?',(self.stream,limit))]
    def predict(self):return self.predictor.distribution(list(self.prediction_tail))
    def prediction_history(self,limit=10):return self.predictor.recent(limit)
    def close(self):self.db.close()
