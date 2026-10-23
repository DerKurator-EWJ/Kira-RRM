"""Bestand und Staunen: offene Beziehungen werden zu dauerhaft gespeicherten Fragen.

Die Brücke stellt keine neuen Sinnesdaten her; sie führt vorliegende Beobachtungen
in die InquiryQueue über und aktualisiert den Fragenstatus bei Befundwechsel.
"""
from .bestand import Bestand
from .inquiry_queue import InquiryQueue

class StaunenBruecke:
    def __init__(self, bestand: Bestand, fragen: InquiryQueue):
        self.bestand = bestand
        self.fragen = fragen

    @staticmethod
    def _frage(ganzes, anderes):
        return f"Ist {anderes} Teil von {ganzes} oder nur damit verbunden?"

    @staticmethod
    def _kontext(ganzes, anderes):
        # JSON vermeidet Kollisionen bei Sonderzeichen in Kennungen.
        import json
        return 'bestand:' + json.dumps([ganzes, anderes], ensure_ascii=False, separators=(',', ':'))

    def beobachten(self, anwesend, gekoppelt=(), gemeinsam_bewegt=()):
        befunde = self.bestand.beobachten(anwesend, gekoppelt, gemeinsam_bewegt)
        ergebnis=[]
        for (ganzes, anderes), befund in sorted(befunde.items()):
            kontext=self._kontext(ganzes, anderes)
            frage=self._frage(ganzes, anderes)
            # Die Frage bleibt auch bei zwischenzeitlich geklärtem Befund nachvollziehbar.
            vorhandene=next((x for x in self.fragen.list() if x['context']==kontext and x['question']==frage),None)
            if befund.art=='offen':
                if vorhandene is None:
                    qid=self.fragen.propose(kontext,frage,relevance=1,uncertainty=1-befund.sicherheit,gain=1,cost=1)
                    aktion='gefragt'
                elif vorhandene['status']!='open':
                    self.fragen.resume(vorhandene['id'],'Befund wieder offen: '+befund.grund)
                    qid=vorhandene['id'];aktion='wieder_geoeffnet'
                else:
                    qid=vorhandene['id'];aktion='bleibt_offen'
            else:
                if vorhandene is None:
                    qid=self.fragen.propose(kontext,frage,relevance=1,uncertainty=0,gain=1,cost=1)
                else: qid=vorhandene['id']
                if (vorhandene is None or vorhandene['status']!='resolved'
                    or not vorhandene['last_reason'].startswith('Vorläufiger Befund '+befund.art+':')):
                    self.fragen.resolve(qid,f'Vorläufiger Befund {befund.art}: {befund.grund}')
                    aktion='vorlaeufig_geklaert'
                else: aktion='bleibt_geklaert'
            ergebnis.append({'paar':[ganzes,anderes],'befund':befund.art,'frage_id':qid,'aktion':aktion})
        return ergebnis
