import unittest, tempfile, os
from foundation.inquiry_queue import InquiryQueue
from foundation.epistemic_regulation import EpistemicCore

class InquiryTests(unittest.TestCase):
    def test_priority(self):
        q=InquiryQueue(); a=q.propose('a','a',gain=1);b=q.propose('b','b',gain=3);self.assertEqual(q.next()['id'],b);q.close()
    def test_budget(self):
        q=InquiryQueue(budget=1);q.propose('a','a',cost=2);self.assertIsNone(q.investigate());q.close()
    def test_investigation_deferred(self):
        q=InquiryQueue();i=q.propose('a','a');self.assertEqual(q.investigate()['id'],i);self.assertEqual(q.list()[0]['status'],'deferred');q.close()
    def test_resume(self):
        q=InquiryQueue();i=q.propose('a','a');q.defer(i);q.resume(i);self.assertEqual(q.next()['id'],i);q.close()
    def test_resolve(self):
        q=InquiryQueue();i=q.propose('a','a');q.resolve(i);self.assertIsNone(q.next());q.close()
    def test_revision_reopens(self):
        q=InquiryQueue();i=q.propose('a','a');q.resolve(i);self.assertEqual(q.reopen_on_revision('a'),1);self.assertEqual(q.next()['id'],i);q.close()
    def test_revision_scoped(self):
        q=InquiryQueue();a=q.propose('a','a');b=q.propose('b','b');q.resolve(a);q.resolve(b);q.reopen_on_revision('a');self.assertEqual(q.list('resolved')[0]['id'],b);q.close()
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,'q.sqlite');q=InquiryQueue(p);i=q.propose('a','a');q.defer(i);q.close();q=InquiryQueue(p);self.assertEqual(q.list()[0]['status'],'deferred');q.close()
    def test_dedupe(self):
        q=InquiryQueue();a=q.propose('a','a');b=q.propose('a','a',gain=3);self.assertEqual(a,b);self.assertEqual(len(q.list()),1);q.close()
    def test_invalid(self):
        q=InquiryQueue()
        for args in [('a','',1,1,1,1),('a','a',1,1,1,0),('a','a',1,float('nan'),1,1)]:
            with self.assertRaises(ValueError):q.propose(*args)
        q.close()
    def test_events(self):
        q=InquiryQueue();i=q.propose('a','a');q.defer(i,'wait');q.resume(i,'new');self.assertEqual(q.events(i),[('defer','wait'),('resume','new')]);q.close()
    def test_epistemic_bridge(self):
        q=InquiryQueue();e=EpistemicCore(threshold=3,budget=100);i=q.propose('a','why');q.resolve(i)
        for x in ['B']*5+['C']*14:
            result=e.observe('a',x)
            if result['action']=='revise':q.reopen_on_revision('a')
        self.assertEqual(q.list()[0]['status'],'open');e.close();q.close()
