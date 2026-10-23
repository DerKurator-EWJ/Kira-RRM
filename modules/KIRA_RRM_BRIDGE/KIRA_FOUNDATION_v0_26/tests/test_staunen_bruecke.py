import unittest,tempfile
from pathlib import Path
from foundation.bestand import Bestand
from foundation.inquiry_queue import InquiryQueue
from foundation.staunen_bruecke import StaunenBruecke
from foundation.wortbruecke import technisch,deutsch,begriffe

class StaunenTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.q=InquiryQueue(str(Path(self.tmp.name)/'q.sqlite'))
        self.br=StaunenBruecke(Bestand(),self.q)
    def tearDown(self):
        self.q.close();self.tmp.cleanup()
    def test_frage_entsteht(self):
        r=self.br.beobachten(['A','B'],[('A','B')],[('A','B')]);self.assertEqual(r[0]['aktion'],'gefragt');self.assertEqual(len(self.q.list('open')),1)
    def test_keine_doppelten_fragen(self):
        for _ in range(2):self.br.beobachten(['A','B'],[('A','B')],[('A','B')])
        self.assertEqual(len(self.q.list()),1)
    def test_festigung_schliesst(self):
        for _ in range(3):r=self.br.beobachten(['A','B'],[('A','B')],[('A','B')])
        self.assertEqual(r[0]['befund'],'teil');self.assertEqual(self.q.list()[0]['status'],'resolved')
    def test_trennung_revidiert(self):
        for _ in range(3):self.br.beobachten(['A','B'],[('A','B')],[('A','B')])
        r=self.br.beobachten(['A','B']);self.assertEqual(r[0]['befund'],'verbunden');self.assertEqual(self.q.list()[0]['status'],'resolved')
        self.assertIn('verbunden',self.q.list()[0]['last_reason'])
    def test_uebergang_wieder_offen(self):
        self.br.beobachten(['A','B'],[('A','B')],[('A','B')]);self.q.defer(self.q.list()[0]['id'])
        r=self.br.beobachten(['A','B'],[('A','B')],[('A','B')]);self.assertEqual(r[0]['aktion'],'wieder_geoeffnet')
    def test_sonderzeichen_kontext(self):
        a=self.br._kontext('A:B','C');b=self.br._kontext('A','B:C');self.assertNotEqual(a,b)
    def test_persistenz(self):
        self.br.beobachten(['A','B'],[('A','B')]);self.assertEqual(len(self.q.list()),1)
        self.q.close();self.q=InquiryQueue(str(Path(self.tmp.name)/'q.sqlite'));self.assertEqual(len(self.q.list()),1)
    def test_wortbruecke(self):
        self.assertEqual(technisch('Staunen'),'Inquiry');self.assertEqual(deutsch('Inquiry'),'Staunen')
    def test_begriffe_eindeutig(self):
        codes=[v['code'] for v in begriffe().values()];self.assertEqual(len(codes),len(set(codes)))
    def test_unbekannt(self):
        with self.assertRaises(KeyError):technisch('Unbekannt')
