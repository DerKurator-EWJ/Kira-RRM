"""Bestand: Beobachtete Teilhabe von vorübergehender Verbindung trennen.

Arbeitet mit allgemeinen Kennungen und Beobachtungsfolgen, nicht mit Pixeln.
Klassifikationen sind begründete Vermutungen, keine Ontologiebeweise.
"""
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class Befund:
    ganzes: str
    anderes: str
    art: str  # 'teil', 'verbunden', 'offen'
    sicherheit: float
    grund: str
    gemeinsam: int
    getrennt: int


class Bestand:
    """Sammelt zeitliche Belege für 'Teil von' und 'verbunden mit'.

    Jede Beobachtung ist eine Menge von Paaren (Ganzes, anderes), die
    gerade gekoppelt sind, und eine Menge unabhängig beobachteter Kennungen.
    Explizite Trennungen zählen stärker als gemeinsame Beobachtungen.
    """
    def __init__(self, mindest_belege=3):
        if not isinstance(mindest_belege,int) or mindest_belege<2:
            raise ValueError('mindest_belege muss >= 2 sein')
        self.mindest_belege=mindest_belege
        self.schritt=0
        self.belege={}
        self.verlauf=[]

    def beobachten(self, anwesend, gekoppelt=(), gemeinsam_bewegt=()):
        anwesend=set(anwesend)
        gekoppelt={tuple(p) for p in gekoppelt}
        gemeinsam_bewegt={tuple(p) for p in gemeinsam_bewegt}
        for paar in gekoppelt|gemeinsam_bewegt:
            if len(paar)!=2 or paar[0]==paar[1] or not set(paar)<=anwesend:
                raise ValueError('Beziehung erfordert zwei verschiedene anwesende Kennungen')
        self.schritt+=1
        # Nur explizit registrierte Beziehungen werden bewertet.
        for paar in gekoppelt|gemeinsam_bewegt:
            self.belege.setdefault(paar,{'zusammen':0,'bewegung':0,'getrennt':0,'zuletzt':0})
        for paar,werte in self.belege.items():
            a,b=paar
            if a not in anwesend or b not in anwesend: continue
            if paar in gekoppelt:
                werte['zusammen']+=1
                if paar in gemeinsam_bewegt: werte['bewegung']+=1
            else:
                werte['getrennt']+=1
            werte['zuletzt']=self.schritt
        neu={paar:self.befund(*paar) for paar in self.belege}
        for paar,b in neu.items():
            vorher=next((v['art'] for v in reversed(self.verlauf) if tuple(v['paar'])==paar),None)
            if vorher!=b.art:
                self.verlauf.append({'schritt':self.schritt,'paar':list(paar),'vorher':vorher,'art':b.art,'grund':b.grund})
        return neu

    def befund(self,ganzes,anderes):
        d=self.belege.get((ganzes,anderes))
        if d is None: return Befund(ganzes,anderes,'offen',0.,'Keine gemeinsamen Beobachtungen',0,0)
        z,t,b=d['zusammen'],d['getrennt'],d['bewegung']
        # Ein beobachtetes Auseinandergehen ist ein Gegenbeleg für feste Teilhabe.
        if t>=1 and z>=1:
            return Befund(ganzes,anderes,'verbunden',round(t/(t+z),3),'Beide getrennt beobachtet; feste Teilhabe nicht gestützt',z,t)
        if z>=self.mindest_belege and b>=self.mindest_belege and t==0:
            return Befund(ganzes,anderes,'teil',round(min(z,b)/(min(z,b)+self.mindest_belege),3),'Wiederholt gekoppelt und gemeinsam bewegt; vorläufige Teil-Vermutung',z,t)
        return Befund(ganzes,anderes,'offen',round(z/(z+self.mindest_belege),3),'Beobachtungen reichen noch nicht zur Unterscheidung',z,t)

    def fragen(self):
        """Offene, untersuchbare Fragen, keine vorgefertigte natürliche Sprache-KI."""
        return [{'paar':list(p),'frage':f'Ist {p[1]} Teil von {p[0]} oder nur damit verbunden?',
                 'grund':self.befund(*p).grund} for p in sorted(self.belege) if self.befund(*p).art=='offen']

    def speichern(self,pfad):
        pfad=Path(pfad); pfad.parent.mkdir(parents=True,exist_ok=True)
        daten={'fassung':1,'mindest_belege':self.mindest_belege,'schritt':self.schritt,
               'belege':[{'paar':list(p),'werte':v} for p,v in sorted(self.belege.items())], 'verlauf':self.verlauf}
        tmp=pfad.with_suffix(pfad.suffix+'.tmp')
        tmp.write_text(json.dumps(daten,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(pfad)

    @classmethod
    def laden(cls,pfad):
        daten=json.loads(Path(pfad).read_text(encoding='utf-8'))
        if daten.get('fassung')!=1: raise ValueError('Unbekannte Fassung')
        obj=cls(daten['mindest_belege']); obj.schritt=daten['schritt']
        obj.belege={tuple(x['paar']):x['werte'] for x in daten['belege']}; obj.verlauf=daten['verlauf']
        return obj
