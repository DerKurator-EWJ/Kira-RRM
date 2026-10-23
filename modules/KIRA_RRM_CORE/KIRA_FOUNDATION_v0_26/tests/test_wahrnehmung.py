import unittest
from foundation.wahrnehmung import Spur, MerkmalsMass, Zusammenhang, Blicktiefe, Wahrnehmung
class TestWahrnehmung(unittest.TestCase):
    def setUp(self):
        self.s=[Spur('bild','a',(.1,.2),('b',)),Spur('bild','b',(.11,.21),('a','c')),Spur('bild','c',(.9,.8),('b',))]
    def test_bindung(self):
        self.assertEqual([b.mitglieder for b in Zusammenhang(.1).binden(self.s)],[('a','b'),('c',)])
    def test_modalitaeten(self):
        a=Wahrnehmung().ordnen(self.s)
        b=Wahrnehmung().ordnen([Spur('ton',s.zeichen,s.merkmale,s.nachbarn) for s in self.s])
        self.assertEqual([x.mitglieder for x in a['baender']],[x.mitglieder for x in b['baender']])
        self.assertEqual(a['spuren'],b['spuren'])
    def test_kennung(self):
        self.assertEqual(MerkmalsMass().kennung(self.s[0]),MerkmalsMass().kennung(self.s[0]))
    def test_reihenfolge(self):
        self.assertEqual([b.mitglieder for b in Zusammenhang(.1).binden(reversed(self.s))],[('a','b'),('c',)])
    def test_keine_nachbarschaft(self):
        self.assertEqual(len(Zusammenhang(5).binden([Spur('x','a',(1,)),Spur('x','b',(1,))])),2)
    def test_dimensionen(self):
        with self.assertRaises(ValueError): Zusammenhang().binden([Spur('x','a',(1,)),Spur('x','b',(1,2))])
    def test_duplikate(self):
        with self.assertRaises(ValueError): Zusammenhang().binden([self.s[0],self.s[0]])
    def test_nan(self):
        with self.assertRaises(ValueError): Spur('x','a',(float('nan'),))
    def test_budget(self):
        self.assertEqual(Blicktiefe().waehlen([('a',1,1),('b',9,2)],2),['b'])
    def test_budget_null(self):
        self.assertEqual(Blicktiefe().waehlen([('a',1,1)],0),[])
    def test_ungültige_grenze(self):
        with self.assertRaises(ValueError): Zusammenhang(-1)
    def test_leer(self):
        self.assertEqual(Wahrnehmung().ordnen([])['baender'],[])
