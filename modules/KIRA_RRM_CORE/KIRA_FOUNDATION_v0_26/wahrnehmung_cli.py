"""Drei Datenquellen, dieselben Kernwerkzeuge."""
from foundation.wahrnehmung import Spur, Wahrnehmung, Blicktiefe

def zeigen(titel, spuren):
    ergebnis=Wahrnehmung(schritt=.1,grenze=.25).ordnen(spuren)
    print('\n'+titel)
    for band in ergebnis['baender']:
        print('  Verbund:',', '.join(band.mitglieder))

zeigen('BILD: benachbarte Farbflaechen',[
    Spur('bild','feld1',(.2,.5),('feld2',)),
    Spur('bild','feld2',(.21,.52),('feld1','feld3')),
    Spur('bild','feld3',(.9,.1),('feld2',))])
zeigen('TON: benachbarte Klangabschnitte',[
    Spur('ton','klang1',(.2,.5),('klang2',)),
    Spur('ton','klang2',(.21,.52),('klang1','klang3')),
    Spur('ton','klang3',(.9,.1),('klang2',))])
zeigen('TEXT: benachbarte Textabschnitte (Beispielmerkmale)',[
    Spur('text','teil1',(.2,.5),('teil2',)),
    Spur('text','teil2',(.21,.52),('teil1','teil3')),
    Spur('text','teil3',(.9,.1),('teil2',))])
print('\nBlicktiefe:',Blicktiefe().waehlen([('bekannt',1,2),('unklar',8,3),('neu',4,2)],5))
print('Hinweis: Die Textmerkmale sind Testwerte, kein Sprachverstaendnis.')
