import os,tempfile,unittest
from bridge import KiraBridge
from foundation.wiedererkennung import Sicht

class BridgeTests(unittest.TestCase):
    def test_identity_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=os.path.join(tmp,'k.sqlite')
            b=KiraBridge(p)
            a=b.recognize([Sicht('frame1',(.2,.3))])['frame1']; b.close()
            b=KiraBridge(p)
            c=b.recognize([Sicht('frame2',(.21,.3))])['frame2']
            self.assertEqual(a['object_id'],c['object_id'])
            self.assertEqual(a['rrm_handle'],c['rrm_handle'])
            b.close()

    def test_observe_shared_store_and_prediction(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=KiraBridge(os.path.join(tmp,'k.sqlite'),cache_budget=64)
            def state(rel):return {'nodes':{'a':'point','b':'point'},'edges':[['a',rel,'b']]}
            for _ in range(3): b.observe('test',state('near')); b.observe('test',state('far'))
            self.assertEqual(b.rrm.predict('test',state('near'),contextual=False)['result'],state('far'))
            self.assertEqual(b.rrm.stats()['observations'],6)
            self.assertEqual(b.rrm.db.execute('SELECT COUNT(*) FROM bridge_events').fetchone()[0],6)
            b.close()

    def test_relationship_questions_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=os.path.join(tmp,'k.sqlite'); b=KiraBridge(p)
            b.relationships(['a','b'],[('a','b')])
            self.assertEqual(len(b.queue.list('open')),1)
            handle=b.identity_handle('object','a'); b.close()
            b=KiraBridge(p)
            self.assertEqual(b.identity_handle('object','a'),handle)
            self.assertEqual(len(b.queue.list('open')),1)
            for _ in range(2):b.relationships(['a','b'],[('a','b')],[('a','b')])
            # Need three shared-motion observations to infer part
            b.relationships(['a','b'],[('a','b')],[('a','b')])
            self.assertEqual(b.bestand.befund('a','b').art,'teil')
            self.assertEqual(len(b.queue.list('resolved')),1)
            b.close()

    def test_dream_no_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=KiraBridge(os.path.join(tmp,'k.sqlite'))
            s={'nodes':{'a':'point','b':'point'},'edges':[['a','near','b']]}
            before=b.rrm.stats()
            b.rrm.dream('x',s,steps=2)
            self.assertEqual(before,b.rrm.stats())
            b.close()

if __name__=='__main__':unittest.main()
