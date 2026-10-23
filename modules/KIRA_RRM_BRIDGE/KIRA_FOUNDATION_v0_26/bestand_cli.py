from foundation.bestand import Bestand
from pathlib import Path

k=Bestand(mindest_belege=3)
print('KIRA – Bestand: Teil oder Verbindung?')
for i in range(3):
    k.beobachten(['Figur','Arm','Hut'], [('Figur','Arm'),('Figur','Hut')], [('Figur','Arm'),('Figur','Hut')])
    print('Schritt',i+1,'Arm:',k.befund('Figur','Arm').art,'Hut:',k.befund('Figur','Hut').art)
print('Offene Fragen:',k.fragen())
k.beobachten(['Figur','Arm','Hut'], [('Figur','Arm')], [('Figur','Arm')])
print('Hut abgenommen:',k.befund('Figur','Hut'))
print('Arm:',k.befund('Figur','Arm'))
print('Umbaugeschichte:',k.verlauf)
pfad=Path('data')/'bestand_demo.json'; k.speichern(pfad)
print('Gespeichert:',pfad)
