from pathlib import Path
from foundation.wiedererkennung import Wiedererkennung, Sicht
from foundation.inquiry_queue import InquiryQueue
from foundation.identitaetsfragen import Identitaetsfragen

Path('data').mkdir(exist_ok=True)
fragen=InquiryQueue('data/identitaet_v26.sqlite')
kira=Identitaetsfragen(Wiedererkennung(merkmal_grenze=1.0),fragen,abstandsspielraum=.2)
try:
    for name, sichten in [('Anfang',[Sicht('a',(0.,)),Sicht('b',(0.8,))]),
                          ('Mehrdeutig',[Sicht('x',(0.4,))]),
                          ('Eindeutig',[Sicht('x',(0.0,))])]:
        print(name, kira.beobachten(sichten))
    print('Gespeicherte Fragen:',fragen.list())
finally:
    fragen.close()
