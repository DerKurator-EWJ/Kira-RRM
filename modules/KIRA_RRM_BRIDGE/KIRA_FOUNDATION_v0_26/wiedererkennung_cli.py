from foundation.wiedererkennung import Wiedererkennung, Sicht

kira=Wiedererkennung(merkmal_grenze=.3,lage_grenze=2,geduld=2)
folgen=[
    [Sicht('fleck_a',(.2,.5),(0,0)),Sicht('fleck_b',(.9,.1),(9,0))],
    [Sicht('neues_bildfeld',(.21,.51),(1,0)),Sicht('anderer_name',(.9,.11),(8,0))],
    [Sicht('wieder',(.23,.52),(2,0))],
]
for nr,sichten in enumerate(folgen,1):
    print('Beobachtung',nr,':',kira.beobachten(sichten))
print('Die Kennungen sind Zuordnungshypothesen, kein Nachweis echter Identitaet.')
