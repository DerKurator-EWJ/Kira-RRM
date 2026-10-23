"""Persistent inquiry queue: priorities are scheduling heuristics, not emotions."""
import sqlite3
import math

class InquiryQueue:
    def __init__(self, path=":memory:", budget=5):
        if budget < 1: raise ValueError("budget must be positive")
        self.db=sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, context TEXT NOT NULL, question TEXT NOT NULL, relevance REAL NOT NULL, uncertainty REAL NOT NULL, gain REAL NOT NULL, cost REAL NOT NULL, status TEXT NOT NULL DEFAULT 'open', attempts INTEGER NOT NULL DEFAULT 0, last_reason TEXT NOT NULL DEFAULT '', UNIQUE(context,question))")
        self.db.execute("CREATE TABLE IF NOT EXISTS inquiry_events (id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL, action TEXT NOT NULL, reason TEXT NOT NULL)")
        self.db.commit()
        self.budget=budget
        self.remaining=budget

    def reset_budget(self): self.remaining=self.budget

    def propose(self,context,question,relevance=1,uncertainty=1,gain=1,cost=1):
        if not isinstance(context,str) or not context.strip() or not isinstance(question,str) or not question.strip(): raise ValueError("context and question required")
        vals=(relevance,uncertainty,gain,cost)
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in vals) or cost==0: raise ValueError("invalid scores")
        self.db.execute("INSERT INTO questions(context,question,relevance,uncertainty,gain,cost) VALUES (?,?,?,?,?,?) ON CONFLICT(context,question) DO UPDATE SET relevance=excluded.relevance, uncertainty=excluded.uncertainty, gain=excluded.gain, cost=excluded.cost",(context,question,*vals))
        self.db.commit()
        return self.db.execute("SELECT id FROM questions WHERE context=? AND question=?",(context,question)).fetchone()[0]

    def list(self,status=None):
        sql="SELECT id,context,question,relevance,uncertainty,gain,cost,status,attempts,last_reason FROM questions"
        args=()
        if status is not None: sql+=" WHERE status=?"; args=(status,)
        rows=self.db.execute(sql+" ORDER BY id",args).fetchall()
        keys=('id','context','question','relevance','uncertainty','gain','cost','status','attempts','last_reason')
        return [dict(zip(keys,row)) for row in rows]

    @staticmethod
    def priority(row):
        # Small exploration floor prevents zero uncertainty from permanently suppressing questions.
        return row['relevance']*(0.1+row['uncertainty'])*row['gain']/(row['cost']*(1+row['attempts']))

    def next(self):
        candidates=[r for r in self.list('open') if r['cost']<=self.remaining]
        if not candidates: return None
        return sorted(candidates,key=lambda r:(-self.priority(r),r['id']))[0]

    def _change(self,qid,status,action,reason,attempt=False):
        row=self.db.execute("SELECT status FROM questions WHERE id=?",(qid,)).fetchone()
        if row is None: raise KeyError(qid)
        self.db.execute("UPDATE questions SET status=?, attempts=attempts+?, last_reason=? WHERE id=?",(status,int(attempt),reason,qid))
        self.db.execute("INSERT INTO inquiry_events(question_id,action,reason) VALUES (?,?,?)",(qid,action,reason))
        self.db.commit()

    def investigate(self):
        row=self.next()
        if row is None: return None
        self.remaining-=row['cost']
        self._change(row['id'],'deferred','investigate','awaiting evidence',True)
        return row

    def defer(self,qid,reason='insufficient evidence'):
        self._change(qid,'deferred','defer',reason)

    def resume(self,qid,reason='new evidence'):
        self._change(qid,'open','resume',reason)

    def resolve(self,qid,reason='model explains observations'):
        self._change(qid,'resolved','resolve',reason)

    def reopen_on_revision(self,context,reason='model revised'):
        rows=self.db.execute("SELECT id FROM questions WHERE context=? AND status IN ('resolved','deferred')",(context,)).fetchall()
        for (qid,) in rows: self.resume(qid,reason)
        return len(rows)

    def events(self,qid):
        return self.db.execute("SELECT action,reason FROM inquiry_events WHERE question_id=? ORDER BY id",(qid,)).fetchall()

    def close(self): self.db.close()
