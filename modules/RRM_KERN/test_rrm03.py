import tempfile, unittest
from pathlib import Path
from rrm import canonical
from rrm03 import RuleCore
from rules import induce,apply

def graph(rel, suffix='', extra=False):
    nodes={'a'+suffix:'point','b'+suffix:'point'}
    edges=[['a'+suffix,rel,'b'+suffix]]
    if extra:
        nodes['c'+suffix]='other'
        edges.append(['c'+suffix,'attached','a'+suffix])
    return {'nodes':nodes,'edges':edges}

class TestRules(unittest.TestCase):
    def test_induction_renamed_nodes(self):
        self.assertEqual(induce(graph('near'),graph('far','z')),('point','near','point','far'))
    def test_transfer_new_context(self):
        rule=induce(graph('near'),graph('far'))
        actual=apply(graph('near','q',True),rule)
        self.assertEqual(canonical(actual),canonical(graph('far','q',True)))
    def test_ambiguous_target_refused(self):
        s={'nodes':{'a':'point','b':'point','c':'point'},'edges':[['a','near','b'],['a','near','c']]}
        self.assertIsNone(apply(s,('point','near','point','far')))
    def test_no_unjustified_multiedit(self):
        a=graph('near');b=graph('far');b['edges'].append(['b','another','a'])
        self.assertIsNone(induce(a,b))
    def test_persistence_support_and_separation(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'db.sqlite');k=RuleCore(path)
            for x in [graph('near'),graph('far'),graph('near'),graph('far')]:k.observe('s',x)
            k2=RuleCore(path)
            result=k2.transfer('s',graph('near','q',True))
            self.assertEqual(result['state'],'HYPOTHESIS')
            self.assertEqual(result['support'],2)
            self.assertEqual(canonical(result['result']),canonical(graph('far','q',True)))
            self.assertEqual(k2.transfer('other',graph('near'))['state'],'OPEN')
    def test_competing_rules_refused(self):
        with tempfile.TemporaryDirectory() as d:
            k=RuleCore(str(Path(d)/'db.sqlite'))
            with k.db:
                for rel in ('far','away'):
                    k.db.execute('INSERT INTO rules VALUES (?,?,?,?,?,?)',('s','point','near','point',rel,3))
            self.assertEqual(k.transfer('s',graph('near'))['state'],'OPEN')

if __name__=='__main__':unittest.main()
