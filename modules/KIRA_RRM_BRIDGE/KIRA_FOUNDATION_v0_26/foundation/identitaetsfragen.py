"""Identität und Staunen: Mehrdeutige Wiedererkennung als prüfbare Frage.

Die Brücke verwendet Merkmals- und Lageabstände. Ein Gleichstand ist keine
bewiesene Identität. Die bisherige Wiedererkennung bleibt unverändert.
"""
from math import dist, isfinite
import json
from .wiedererkennung import Wiedererkennung, Sicht
from .inquiry_queue import InquiryQueue

class Identitaetsfragen:
    def __init__(self, wiedererkennung: Wiedererkennung, fragen: InquiryQueue, abstandsspielraum=0.15):
        if not isfinite(abstandsspielraum) or abstandsspielraum < 0:
            raise ValueError('abstandsspielraum muss endlich und nichtnegativ sein')
        self.wiedererkennung = wiedererkennung
        self.fragen = fragen
        self.abstandsspielraum = abstandsspielraum
        self.letzte_zuordnung = {}

    @staticmethod
    def _kontext(zeichen):
        return 'identitaet:' + json.dumps(zeichen, ensure_ascii=False)

    @staticmethod
    def _frage(zeichen):
        return f'Welches bekannte Ding zeigt die Sicht {zeichen}?'

    def _kandidaten(self, sicht):
        w = self.wiedererkennung
        ergebnis=[]
        for kennung, ding in w.dinge.items():
            if w.schritt + 1 - ding['zuletzt'] > w.geduld + 1:
                continue
            if len(sicht.merkmale)!=len(ding['merkmale']) or len(sicht.lage)!=len(ding['lage']):
                continue
            m=dist(sicht.merkmale,ding['merkmale'])
            l=dist(sicht.lage,ding['lage']) if sicht.lage else 0.0
            if m<=w.merkmal_grenze and l<=w.lage_grenze:
                wert=m/max(w.merkmal_grenze,1e-12)+l/max(w.lage_grenze,1e-12)
                ergebnis.append((wert,kennung))
        return sorted(ergebnis)

    def beobachten(self, sichten):
        sichten=list(sichten)
        if not all(isinstance(s,Sicht) for s in sichten):
            raise TypeError('Sichten erwartet')
        if len({s.zeichen for s in sichten})!=len(sichten):
            raise ValueError('Doppelte Sichtzeichen')
        kandidaten={s.zeichen:self._kandidaten(s) for s in sichten}
        zuordnung=self.wiedererkennung.beobachten(sichten)
        ergebnisse=[]
        for s in sichten:
            optionen=kandidaten[s.zeichen]
            mehrdeutig=len(optionen)>=2 and optionen[1][0]-optionen[0][0]<=self.abstandsspielraum
            # Auch ein Konflikt um dieselbe Kennung zwischen mehreren Sichten ist offen.
            konkurrierend=any(anderes!=s.zeichen and any(k==zuordnung[s.zeichen] for _,k in kandidaten[anderes]) for anderes in kandidaten)
            offen=mehrdeutig or konkurrierend
            kontext=self._kontext(s.zeichen); frage=self._frage(s.zeichen)
            vorhanden=next((r for r in self.fragen.list() if r['context']==kontext and r['question']==frage),None)
            qid=None
            if offen:
                if vorhanden is None:
                    qid=self.fragen.propose(kontext,frage,relevance=1,uncertainty=1,gain=1,cost=1)
                    aktion='gefragt'
                else:
                    qid=vorhanden['id']
                    if vorhanden['status']!='open':
                        self.fragen.resume(qid,'Mehrdeutige Wiedererkennung')
                        aktion='wieder_geoeffnet'
                    else: aktion='bleibt_offen'
            elif vorhanden is not None:
                qid=vorhanden['id']
                if vorhanden['status']!='resolved':
                    self.fragen.resolve(qid,'Zuordnung derzeit eindeutig; kein Identitätsbeweis')
                    aktion='vorlaeufig_geklaert'
                else: aktion='bleibt_geklaert'
            else: aktion='keine_frage'
            ergebnisse.append({'sicht':s.zeichen,'ding':zuordnung[s.zeichen],
                               'kandidaten':[k for _,k in optionen], 'offen':offen,
                               'frage_id':qid,'aktion':aktion})
        self.letzte_zuordnung=zuordnung
        return ergebnisse
