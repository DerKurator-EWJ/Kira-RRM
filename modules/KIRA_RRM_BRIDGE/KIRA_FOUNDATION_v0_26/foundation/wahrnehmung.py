"""Kiras gemeinsame Wahrnehmungswerkzeuge, unabhängig von der Datenquelle.

Die Adapter bestimmen die Merkmale. Der Kern verarbeitet nur Messwerte,
Nachbarschaften und Relationen. Keine automatische Semantik oder Objekterkennung.
"""
from dataclasses import dataclass, field
from math import isfinite, dist
from hashlib import sha256
import json

@dataclass(frozen=True)
class Spur:
    quelle: str
    zeichen: str
    merkmale: tuple[float, ...]
    nachbarn: tuple[str, ...] = ()
    zeit: float = 0.0

    def __post_init__(self):
        if not self.quelle or not self.zeichen: raise ValueError('Quelle und Zeichen fehlen')
        if not self.merkmale or any(not isfinite(x) for x in self.merkmale): raise ValueError('Merkmale müssen endlich sein')
        if not isfinite(self.zeit): raise ValueError('Zeit muss endlich sein')

@dataclass(frozen=True)
class Band:
    zeichen: str
    mitglieder: tuple[str, ...]
    quelle: str

class MerkmalsMass:
    """Ordnet ähnliche Vektoren einer festen, nachvollziehbaren Kennung zu."""
    def __init__(self, schritt=0.1):
        if not isfinite(schritt) or schritt <= 0: raise ValueError('Schritt muss positiv sein')
        self.schritt=schritt

    def kennung(self, spur):
        # Deterministisch, unabhängig von Python hash() und der Quellmodalität.
        werte=tuple(round(x/self.schritt) for x in spur.merkmale)
        payload=json.dumps(werte,separators=(',',':')).encode('ascii')
        return sha256(payload).hexdigest()[:16]

class Zusammenhang:
    """Bildet Gruppen nur über explizite Nachbarschaft und Merkmalsnähe."""
    def __init__(self, grenze=0.3):
        if not isfinite(grenze) or grenze<0: raise ValueError('Grenze muss >= 0 sein')
        self.grenze=grenze

    def binden(self, spuren):
        spuren=list(spuren)
        ids=[s.zeichen for s in spuren]
        if len(ids)!=len(set(ids)): raise ValueError('Doppelte Zeichen')
        if len({len(s.merkmale) for s in spuren})>1: raise ValueError('Unterschiedliche Merkmalsdimensionen')
        by_id={s.zeichen:s for s in spuren}
        adj={s.zeichen:set() for s in spuren}
        for s in spuren:
            for n in s.nachbarn:
                if n not in by_id or n==s.zeichen: continue
                if dist(s.merkmale,by_id[n].merkmale)<=self.grenze:
                    adj[s.zeichen].add(n); adj[n].add(s.zeichen)
        result=[]; seen=set()
        for start in sorted(by_id):
            if start in seen: continue
            todo=[start]; seen.add(start); group=[]
            while todo:
                cur=todo.pop(); group.append(cur)
                for n in sorted(adj[cur]):
                    if n not in seen: seen.add(n); todo.append(n)
            members=tuple(sorted(group))
            # Gruppenkennungen beschreiben die beobachteten Mitglieder, nicht eine zeitlich stabile Objekt-ID.
            tag=sha256(json.dumps(members).encode()).hexdigest()[:16]
            result.append(Band(tag,members,','.join(sorted({by_id[m].quelle for m in members}))))
        return result

class Blicktiefe:
    """Wählt Messungen unter einem festen Budget nach Priorität aus."""
    def waehlen(self, kandidaten, budget):
        if not isinstance(budget,int) or budget<0: raise ValueError('Ungültiges Budget')
        # (Kennung, Priorität, Kosten); feste Reihenfolge bei Gleichstand.
        kandidaten=list(kandidaten)
        if len({k[0] for k in kandidaten})!=len(kandidaten): raise ValueError('Doppelte Kennungen')
        for name,wert,kosten in kandidaten:
            if not isfinite(wert) or wert<0 or not isinstance(kosten,int) or kosten<=0: raise ValueError('Ungültiger Kandidat')
        rest=budget; out=[]
        for name,wert,kosten in sorted(kandidaten,key=lambda k:(-k[1]/k[2],str(k[0]))):
            if kosten<=rest: out.append(name); rest-=kosten
        return out

class Wahrnehmung:
    """Gemeinsamer Ablauf für bereits extrahierte Merkmale."""
    def __init__(self,schritt=0.1,grenze=0.3):
        self.mass=MerkmalsMass(schritt)
        self.bindung=Zusammenhang(grenze)

    def ordnen(self,spuren):
        spuren=list(spuren)
        baender=self.bindung.binden(spuren)
        return {'spuren':[(s.zeichen,self.mass.kennung(s)) for s in spuren],
                'baender':baender}
