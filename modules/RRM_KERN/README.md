# RRM-KERN 0.5 — Konsolidierung statt Funktionswachstum

Python 3.9+, nur Standardbibliothek. `python -m unittest -v` im Ordner ausführen.

**Änderung gegenüber 0.4:** Ein einziges Evidenzschema speichert beobachtete Änderungen und unveränderte Relationen. Kontextabhängige und kontextfreie Vorhersagen sind jetzt zwei **Abfragen derselben Evidenz**, keine zwei unabhängig lernenden Modelle. `dream` führt dieselbe Fortsetzungsoperation wiederholt aus und speichert ihre Hypothesen nicht als Beobachtungen.

**Was es nicht ist:** keine fertige ID-Bitsyntax, keine vollständige RRM-Sprache, keine allgemeine KI. Die formale Vorstufe steht in `SPRACHE.md`.

Beispiel:

```python
from rrm05 import Kernel
k=Kernel('kira.sqlite')
a={'nodes':{'a':'point','b':'point'},'edges':[['a','near','b']]}
b={'nodes':a['nodes'],'edges':[['a','far','b']]}
for s in (a,b,a,b,a): k.observe('camera',s)
print(k.predict('camera',a,focus=0,contextual=False))
```

**Messziel der Version:** Vereinheitlichung der Evidenz, nicht Leistungsgewinn. Es gibt noch keine Laufzeit- oder Speicherbenchmarks gegenüber 0.4.
