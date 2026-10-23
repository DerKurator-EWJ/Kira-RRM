"""Wiedererkennung von Bändern über Beobachtungsfolgen, ohne Medienbindung.

Eine Kennung ist eine Arbeitshypothese über Fortbestand, kein Identitätsbeweis.
"""
from dataclasses import dataclass
from math import dist, isfinite
from pathlib import Path
import json

@dataclass(frozen=True)
class Sicht:
    """Ein beobachtetes Band: Kennung im aktuellen Schritt, Merkmale, optionale Lage."""
    zeichen: str
    merkmale: tuple[float, ...]
    lage: tuple[float, ...] = ()
    def __post_init__(self):
        if not self.zeichen or not self.merkmale or any(not isfinite(v) for v in self.merkmale+self.lage):
            raise ValueError('Ungültige Sicht')

class Wiedererkennung:
    """Einfacher deterministischer Zuordner mit maximaler Beobachtungslücke."""
    def __init__(self, merkmal_grenze=.35, lage_grenze=2., geduld=2):
        if not isfinite(merkmal_grenze) or merkmal_grenze<0 or not isfinite(lage_grenze) or lage_grenze<0 or not isinstance(geduld,int) or geduld<0:
            raise ValueError('Ungültige Grenzen')
        self.merkmal_grenze=merkmal_grenze; self.lage_grenze=lage_grenze; self.geduld=geduld
        self.schritt=0; self.naechste_id=1; self.dinge={}

    def beobachten(self, sichten):
        sichten=list(sichten)
        if len({s.zeichen for s in sichten})!=len(sichten): raise ValueError('Doppelte Sichtzeichen')
        self.schritt+=1
        kandidaten=[]
        for s in sichten:
            for kennung,d in self.dinge.items():
                if self.schritt-d['zuletzt']>self.geduld+1: continue
                if len(s.merkmale)!=len(d['merkmale']) or len(s.lage)!=len(d['lage']): continue
                m=dist(s.merkmale,d['merkmale']); l=dist(s.lage,d['lage']) if s.lage else 0.
                if m<=self.merkmal_grenze and l<=self.lage_grenze:
                    kandidaten.append((m/max(self.merkmal_grenze,1e-12)+l/max(self.lage_grenze,1e-12),kennung,s.zeichen))
        zugeordnet={}; belegte_dinge=set()
        for _,kennung,zeichen in sorted(kandidaten):
            if zeichen not in zugeordnet and kennung not in belegte_dinge:
                zugeordnet[zeichen]=kennung; belegte_dinge.add(kennung)
        for s in sorted(sichten,key=lambda x:x.zeichen):
            kennung=zugeordnet.get(s.zeichen)
            if kennung is None:
                kennung=f'D{self.naechste_id:06d}'; self.naechste_id+=1; zugeordnet[s.zeichen]=kennung
            self.dinge[kennung]={'merkmale':list(s.merkmale),'lage':list(s.lage),'zuletzt':self.schritt}
        self.dinge={k:v for k,v in self.dinge.items() if self.schritt-v['zuletzt']<=self.geduld}
        return {s.zeichen:zugeordnet[s.zeichen] for s in sichten}

    def speichern(self,pfad):
        pfad=Path(pfad); pfad.parent.mkdir(parents=True,exist_ok=True)
        payload={'version':1,'schritt':self.schritt,'naechste_id':self.naechste_id,'dinge':self.dinge,'grenzen':[self.merkmal_grenze,self.lage_grenze,self.geduld]}
        temp=pfad.with_suffix(pfad.suffix+'.tmp'); temp.write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True),encoding='utf-8'); temp.replace(pfad)

    @classmethod
    def laden(cls,pfad):
        payload=json.loads(Path(pfad).read_text(encoding='utf-8'))
        if payload.get('version')!=1: raise ValueError('Unbekannte Speicherfassung')
        obj=cls(*payload['grenzen']); obj.schritt=payload['schritt']; obj.naechste_id=payload['naechste_id']; obj.dinge=payload['dinge']; return obj

def baender_als_sichten(spuren,baender):
    """Bildet Merkmalsmittel aus bestehenden Spurenbändern; keine echte Objektsegmentierung."""
    by_id={s.zeichen:s for s in spuren}
    result=[]
    for band in baender:
        teile=[by_id[n] for n in band.mitglieder]
        if not teile: continue
        dim=len(teile[0].merkmale)
        if any(len(t.merkmale)!=dim for t in teile): raise ValueError('Merkmalsdimensionen passen nicht')
        mittel=tuple(sum(t.merkmale[i] for t in teile)/len(teile) for i in range(dim))
        result.append(Sicht(band.zeichen,mittel))
    return result
