import tempfile,unittest
from pathlib import Path
from rrm04 import ContextCore,examples

def scene(rel='near',flag='red',suffix=''):
    a,b,c=('a'+suffix,'b'+suffix,'c'+suffix)
    return {'nodes':{a:'point',b:'point',c:'signal'},
            'edges':[[a,rel,b],[c,flag,a]]}

class TestContext(unittest.TestCase):
    def test_conditioned_rules_transfer_new_ids(self):
        with tempfile.TemporaryDirectory() as d:
            k=ContextCore(str(Path(d)/'test.db'))
            # Separate streams would isolate learning; use one stream and reset
            # observed last state to avoid cross-example transitions.
            for flag,outcome in [('red','far'),('blue','near')]*3:
                before=scene('near',flag)
                after=scene(outcome,flag)
                k._last.pop('s',None)
                # Write pair evidence directly to avoid synthetic transitions.
                with k.db:
                    for st,old,dt,ctx,result in examples(before,after):
                        k.db.execute('''INSERT INTO contextual_evidence VALUES (?,?,?,?,?,?,1)
                        ON CONFLICT(stream,src_type,old_rel,dst_type,context,outcome)
                        DO UPDATE SET support=support+1''',('s',st,old,dt,ctx,result))
            red=k.explain('s',scene('near','red','z'))
            blue=k.explain('s',scene('near','blue','z'),focus=0)
            self.assertEqual(red['outcome'],'far')
            self.assertEqual(blue['outcome'],'NO_CHANGE')
            self.assertEqual(k.explain('s',scene('near','green'))['state'],'OPEN')
            k.db.close()
            k2=ContextCore(str(Path(d)/'test.db'))
            self.assertEqual(k2.explain('s',scene('near','red'))['outcome'],'far')
    def test_conflict_explicitly_open(self):
        with tempfile.TemporaryDirectory() as d:
            k=ContextCore(str(Path(d)/'test.db'))
            for outcome in ('far','away'):
                for st,old,dt,ctx,result in examples(scene('near'),scene(outcome)):
                    with k.db:k.db.execute('INSERT INTO contextual_evidence VALUES (?,?,?,?,?,?,?)',('s',st,old,dt,ctx,result,2))
            self.assertEqual(k.explain('s',scene())['state'],'OPEN')
    def test_multi_edit_refused(self):
        a=scene();b=scene('far','blue')
        self.assertEqual(examples(a,b),[])
    def test_observe_persists_real_transitions(self):
        with tempfile.TemporaryDirectory() as d:
            k=ContextCore(str(Path(d)/'test.db'))
            for s in [scene('near'),scene('far'),scene('near'),scene('far')]: k.observe('s',s)
            self.assertEqual(k.explain('s',scene('near'))['outcome'],'far')
    def test_dream_not_written_as_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            k=ContextCore(str(Path(d)/'test.db'))
            for s in [scene('near'),scene('far'),scene('near'),scene('far')]:k.observe('s',s)
            before=k.db.execute('SELECT SUM(support) FROM contextual_evidence').fetchone()[0]
            k.explain('s',scene('near'));k.dream('s')
            after=k.db.execute('SELECT SUM(support) FROM contextual_evidence').fetchone()[0]
            self.assertEqual(before,after)
if __name__=='__main__':unittest.main()
