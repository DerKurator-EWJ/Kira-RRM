import tempfile
import unittest
from pathlib import Path
from foundation.wiedererkennung import Sicht, Wiedererkennung, baender_als_sichten
from foundation.wahrnehmung import Spur, Zusammenhang

class TestWiedererkennung(unittest.TestCase):
    def test_gleiche_einheit_bei_neuem_namen(self):
        k=Wiedererkennung()
        a=k.beobachten([Sicht('a',(.2,.3),(0,0))])['a']
        self.assertEqual(a,k.beobachten([Sicht('b',(.21,.31),(1,0))])['b'])
    def test_neue_einheit_bei_grosser_abweichung(self):
        k=Wiedererkennung()
        a=k.beobachten([Sicht('a',(.2,.3))])['a']
        self.assertNotEqual(a,k.beobachten([Sicht('b',(.9,.9))])['b'])
    def test_eindeutige_zuordnung(self):
        k=Wiedererkennung()
        k.beobachten([Sicht('a',(.1,))])
        r=k.beobachten([Sicht('b',(.1,)),Sicht('c',(.11,))])
        self.assertEqual(len(set(r.values())),2)
    def test_luecke(self):
        k=Wiedererkennung(geduld=2)
        a=k.beobachten([Sicht('a',(.1,))])['a']
        k.beobachten([])
        self.assertEqual(a,k.beobachten([Sicht('b',(.1,))])['b'])
    def test_zu_lange_luecke(self):
        k=Wiedererkennung(geduld=1)
        a=k.beobachten([Sicht('a',(.1,))])['a']
        k.beobachten([]);k.beobachten([])
        self.assertNotEqual(a,k.beobachten([Sicht('b',(.1,))])['b'])
    def test_speichern_laden(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'zustand.json';k=Wiedererkennung();a=k.beobachten([Sicht('a',(.1,))])['a'];k.speichern(p)
            self.assertEqual(a,Wiedererkennung.laden(p).beobachten([Sicht('b',(.1,))])['b'])
    def test_ungültige_werte(self):
        with self.assertRaises(ValueError): Sicht('a',(float('nan'),))
    def test_doppelte_zeichen(self):
        with self.assertRaises(ValueError): Wiedererkennung().beobachten([Sicht('a',(1,)),Sicht('a',(2,))])
    def test_verschiedene_dimensionen(self):
        k=Wiedererkennung();a=k.beobachten([Sicht('a',(1,))])['a']
        self.assertNotEqual(a,k.beobachten([Sicht('b',(1,2))])['b'])
    def test_baender_adapter(self):
        sp=[Spur('bild','a',(.1,.2),('b',)),Spur('bild','b',(.11,.21),('a',))]
        baender=Zusammenhang(.1).binden(sp)
        self.assertEqual(len(baender_als_sichten(sp,baender)),1)
    def test_ort_ist_relevant(self):
        k=Wiedererkennung(lage_grenze=1)
        a=k.beobachten([Sicht('a',(.1,),(0,))])['a']
        self.assertNotEqual(a,k.beobachten([Sicht('b',(.1,),(10,))])['b'])
    def test_reihenfolge_deterministisch(self):
        a=[Sicht('z',(.1,)),Sicht('a',(.9,))]
        self.assertEqual(Wiedererkennung().beobachten(a),Wiedererkennung().beobachten(reversed(a)))
