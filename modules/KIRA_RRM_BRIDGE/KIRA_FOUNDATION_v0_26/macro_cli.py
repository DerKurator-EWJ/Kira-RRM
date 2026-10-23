from foundation.macros import OnlineMacroLearner,HierarchicalRouteIndex,exhaustive_probe

def demo():
    learner=OnlineMacroLearner(min_occurrences=3)
    data=[1,2,3,9,1,2,3,8,1,2,3,7,1,2,3,6,1,2,3,5]
    for x in data:learner.observe(x)
    macros=learner.candidates()
    print('KIRA FOUNDATION v0.3 | Online-Makros + Routing')
    print('Ereignisse:',len(data),'| Makrokandidaten:',len(macros))
    for m in macros[:8]:print('ID:',m.macro_id,'Sequenz:',m.tokens,'Vorkommen:',m.occurrences,'Sparpotenzial (Schaetzung):',m.estimated_net_savings)
    idx=HierarchicalRouteIndex()
    for m in macros:idx.register(m)
    probe=[42,1,2,3]
    fast,fc=idx.probe(probe)
    slow,sc=exhaustive_probe(idx,probe)
    print('Probe:',probe,'| Route:',fast,'| Index-Lookups:',fc,'| Vollsuche-Lookups:',sc)
    assert fast==slow
    print('OK: Route und Referenz stimmen ueberein.')
if __name__=='__main__':demo()
