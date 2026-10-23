import unittest
from foundation.wiedererkennung import Wiedererkennung, Sicht
from foundation.inquiry_queue import InquiryQueue
from foundation.identitaetsfragen import Identitaetsfragen

class IdentitaetsfragenTest(unittest.TestCase):
    def setUp(self):
        self.q=InquiryQueue()
        self.k=Identitaetsfragen(Wiedererkennung(merkmal_grenze=1),self.q,.2)
    def tearDown(self): self.q.close()
    def test_ambiguitaet(self):
        self.k.beobachten([Sicht('a',(0.,)),Sicht('b',(0.8,))])
        r=self.k.beobachten([Sicht('x',(0.4,))])[0]
        self.assertTrue(r['offen']); self.assertEqual(r['aktion'],'gefragt')
        self.assertEqual(self.q.list('open')[0]['id'],r['frage_id'])
    def test_aufloesung(self):
        self.k.beobachten([Sicht('a',(0.,)),Sicht('b',(0.8,))])
        self.k.beobachten([Sicht('x',(0.4,))])
        r=self.k.beobachten([Sicht('x',(0.,))])[0]
        self.assertFalse(r['offen']); self.assertEqual(r['aktion'],'vorlaeufig_geklaert')
    def test_neue_sicht_ohne_kandidaten(self):
        self.assertEqual(self.k.beobachten([Sicht('neu',(0.,))])[0]['aktion'],'keine_frage')
    def test_eingabepruefung(self):
        with self.assertRaises(ValueError): self.k.beobachten([Sicht('a',(0.,)),Sicht('a',(1.,))])
        with self.assertRaises(TypeError): self.k.beobachten(['a'])
    def test_grenze(self):
        with self.assertRaises(ValueError): Identitaetsfragen(Wiedererkennung(),self.q,-1)
    def test_kein_zwang_zur_identitaet(self):
        self.k.beobachten([Sicht('a',(0.,)),Sicht('b',(0.8,))])
        r=self.k.beobachten([Sicht('x',(0.4,))])[0]
        self.assertEqual(len(r['kandidaten']),2)
    def test_persistente_frage(self):
        self.k.beobachten([Sicht('a',(0.,)),Sicht('b',(0.8,))])
        r=self.k.beobachten([Sicht('x',(0.4,))])[0]
        self.assertEqual(r['frage_id'],self.q.list()[0]['id'])
