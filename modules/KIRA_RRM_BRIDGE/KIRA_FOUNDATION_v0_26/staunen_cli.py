from pathlib import Path
from foundation.bestand import Bestand
from foundation.inquiry_queue import InquiryQueue
from foundation.staunen_bruecke import StaunenBruecke

Path('data').mkdir(exist_ok=True)
q=InquiryQueue('data/staunen_v25.sqlite')
b=StaunenBruecke(Bestand(mindest_belege=3),q)
try:
    for schritt in range(1,5):
        ergebnis=b.beobachten(['Figur','Hut'],gekoppelt=[('Figur','Hut')],gemeinsam_bewegt=[('Figur','Hut')])
        print('Schritt',schritt,ergebnis)
    print('Hut getrennt:',b.beobachten(['Figur','Hut']))
    print('Fragen:',q.list())
finally:
    q.close()
