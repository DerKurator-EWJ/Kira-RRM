import tempfile
import unittest
from pathlib import Path
from foundation.bestand import Bestand

class TestBestand(unittest.TestCase):
    def test_anfangs_offen(self):
        self.assertEqual(Bestand().befund('a','b').art,'offen')
    def test_teil_nach_gemeinsamer_bewegung(self):
        b=Bestand()
        for _ in range(3): b.beobachten(['a','b'],[('a','b')],[('a','b')])
        self.assertEqual(b.befund('a','b').art,'teil')
    def test_nur_kopplung_ist_nicht_teil(self):
        b=Bestand()
        for _ in range(5): b.beobachten(['a','b'],[('a','b')])
        self.assertEqual(b.befund('a','b').art,'offen')
    def test_trennung_revidiert_teil(self):
        b=Bestand()
        for _ in range(3): b.beobachten(['a','b'],[('a','b')],[('a','b')])
        b.beobachten(['a','b'])
        self.assertEqual(b.befund('a','b').art,'verbunden')
        self.assertEqual(b.verlauf[-1]['vorher'],'teil')
    def test_nicht_anwesend_ist_keine_trennung(self):
        b=Bestand()
        b.beobachten(['a','b'],[('a','b')]); b.beobachten(['a'])
        self.assertEqual(b.befund('a','b').getrennt,0)
    def test_fragen(self):
        b=Bestand(); b.beobachten(['a','b'],[('a','b')])
        self.assertEqual(len(b.fragen()),1)
    def test_richtung_ist_wichtig(self):
        b=Bestand(); b.beobachten(['a','b'],[('a','b')])
        self.assertEqual(b.befund('b','a').gemeinsam,0)
    def test_fehlerhafte_beziehung(self):
        with self.assertRaises(ValueError): Bestand().beobachten(['a'],[('a','b')])
    def test_speichern_laden(self):
        b=Bestand(); b.beobachten(['a','b'],[('a','b')])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bestand.json'; b.speichern(p); c=Bestand.laden(p)
            self.assertEqual(c.befund('a','b'),b.befund('a','b'))
            self.assertEqual(c.schritt,1)
    def test_mindest_belege(self):
        with self.assertRaises(ValueError): Bestand(1)
