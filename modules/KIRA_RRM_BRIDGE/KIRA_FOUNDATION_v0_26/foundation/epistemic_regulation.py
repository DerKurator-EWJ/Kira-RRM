"""Kira Ghost v0.20: bounded, auditable epistemic regulation experiment.
Functional states are scheduling labels, not subjective emotions.
"""
import json
import math
import sqlite3
from collections import Counter

class EpistemicCore:
    def __init__(self, path=":memory:", budget=8, threshold=3):
        if budget < 1 or threshold < 1:
            raise ValueError("budget and threshold must be positive")
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, context TEXT NOT NULL, outcome TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS models (context TEXT PRIMARY KEY, prediction TEXT NOT NULL, version INTEGER NOT NULL, evidence INTEGER NOT NULL, status TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS revisions (id INTEGER PRIMARY KEY, context TEXT NOT NULL, old_prediction TEXT, new_prediction TEXT NOT NULL, reason TEXT NOT NULL, at_observation INTEGER NOT NULL)")
        self.db.commit()
        self.budget = budget
        self.threshold = threshold
        self.spent = 0

    def reset_budget(self):
        self.spent = 0

    def _counts(self, context, window=12):
        rows = self.db.execute("SELECT outcome FROM observations WHERE context=? ORDER BY id DESC LIMIT ?", (context, window)).fetchall()
        return Counter(r[0] for r in rows)

    def observe(self, context, outcome):
        if not isinstance(context, str) or not context or not isinstance(outcome, str) or not outcome:
            raise ValueError("context and outcome must be nonempty strings")
        row = self.db.execute("SELECT prediction,version,evidence,status FROM models WHERE context=?", (context,)).fetchone()
        expected = row[0] if row else None
        surprise = expected is not None and expected != outcome
        cur = self.db.execute("INSERT INTO observations(context,outcome) VALUES (?,?)", (context,outcome))
        counts = self._counts(context)
        # A single contradiction must not destroy a consolidated model.
        candidate, candidate_count = sorted(counts.items(), key=lambda x:(-x[1],x[0]))[0]
        total = sum(counts.values())
        stable = candidate_count >= self.threshold and candidate_count / total >= 0.65
        action = "collect_evidence"
        revised = False
        if row is None:
            if stable and self.spent < self.budget:
                self.spent += 1
                self.db.execute("INSERT INTO models VALUES (?,?,?,?,?)", (context,candidate,1,candidate_count,"consolidated"))
                action = "consolidate"
            else:
                action = "observe"
        elif stable and candidate != expected and self.spent < self.budget:
            self.spent += 1
            self.db.execute("UPDATE models SET prediction=?,version=?,evidence=?,status=? WHERE context=?", (candidate,row[1]+1,candidate_count,"revised",context))
            self.db.execute("INSERT INTO revisions(context,old_prediction,new_prediction,reason,at_observation) VALUES (?,?,?,?,?)", (context,expected,candidate,"recent evidence favors alternative",cur.lastrowid))
            action = "revise"
            revised = True
        elif surprise:
            action = "investigate" if self.spent < self.budget else "defer_budget"
            if action == "investigate":
                self.spent += 1
        elif row:
            action = "maintain"
            if stable and candidate == expected:
                self.db.execute("UPDATE models SET evidence=?,status=? WHERE context=?", (candidate_count,"consolidated",context))
        self.db.commit()
        # Labels summarize internal scheduling, not human emotions.
        state = "revision" if revised else "surprise" if surprise else "satisfaction" if stable else "curiosity"
        return {"context":context,"observed":outcome,"expected_before":expected,"surprise":surprise,"action":action,"state":state,"budget_left":self.budget-self.spent,"model":self.model(context)}

    def model(self, context):
        row = self.db.execute("SELECT prediction,version,evidence,status FROM models WHERE context=?",(context,)).fetchone()
        return None if row is None else dict(zip(("prediction","version","evidence","status"),row))

    def history(self, context):
        rows = self.db.execute("SELECT old_prediction,new_prediction,reason,at_observation FROM revisions WHERE context=? ORDER BY id",(context,)).fetchall()
        return [dict(zip(("old","new","reason","observation_id"),r)) for r in rows]

    def close(self):
        self.db.close()
