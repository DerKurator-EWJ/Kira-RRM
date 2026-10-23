"""Persistent RRM 0.3 hypothesis store atop the 0.2 observation core."""
from collections import Counter
from rrm import RelationalCore, canonical
from rules import induce, apply

class RuleCore(RelationalCore):
    def __init__(self, path='rrm.sqlite'):
        super().__init__(path)
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS rules (stream TEXT, src_type TEXT, old_rel TEXT, dst_type TEXT, new_rel TEXT, support INTEGER NOT NULL, PRIMARY KEY(stream,src_type,old_rel,dst_type,new_rel))')
        self._last = {}

    def observe(self, stream, state):
        previous = self._last.get(stream)
        if previous is None:
            row = self.db.execute('SELECT raw FROM observations WHERE stream=? ORDER BY pos DESC LIMIT 1', (stream,)).fetchone()
            if row:
                import json
                previous = json.loads(row[0])
        result = super().observe(stream, state)
        if previous is not None:
            rule = induce(previous, state)
            if rule:
                with self.db:
                    self.db.execute('INSERT INTO rules VALUES (?,?,?,?,?,1) ON CONFLICT(stream,src_type,old_rel,dst_type,new_rel) DO UPDATE SET support=support+1', (stream, *rule))
        self._last[stream] = state
        return result

    def transfer(self, stream, state, min_support=2):
        """Return one unique best supported applicable rule, or explicit OPEN.
        A tied or competing outcome is not silently resolved.
        """
        rows = self.db.execute('SELECT src_type,old_rel,dst_type,new_rel,support FROM rules WHERE stream=? AND support>=?', (stream,min_support)).fetchall()
        matches = [(tuple(row[:4]),row[4],apply(state,tuple(row[:4]))) for row in rows]
        matches = [(rule,count,out) for rule,count,out in matches if out is not None]
        if not matches:
            return {'state':'OPEN','reason':'no sufficiently supported unambiguous rule'}
        best = max(c for _,c,_ in matches)
        winners = [(rule,c,out) for rule,c,out in matches if c==best]
        if len(winners) != 1:
            return {'state':'OPEN','reason':'competing equally supported rules','candidates':len(winners)}
        rule,count,out = winners[0]
        return {'state':'HYPOTHESIS','rule':rule,'support':count,'result':out,'signature':canonical(out)}
