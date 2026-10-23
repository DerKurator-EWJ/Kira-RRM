# RRM-KERN 0.4 — Kontextabhängige Hypothesen

**Forschungsprototyp, keine allgemeine KI und keine vollständige RRM-Formalisation.**

## Neuer Schritt

Version 0.3 lernte `(point, near, point) -> far` ohne Kontext. 0.4 zählt die Ergebnisse getrennt nach den **lokalen, unveränderten Nachbarrelationen** einer Kante. Aus wiederholten Beobachtungen kann sich beispielsweise ergeben:

- Wenn eine `signal --red--> point`-Relation anliegt, wurde `point --near--> point` zu `far`.
- Wenn stattdessen `signal --blue--> point` anliegt, blieb `near` unverändert (`NO_CHANGE`).
- Bei unbekanntem Kontext `green` bleibt die Fortsetzung `OPEN`.

Das ist **kontextbedingte Korrelation**, kein Nachweis einer Ursache. Gleich häufig beobachtete Ausgänge werden als `OPEN` ausgewiesen. Bei mehrdeutigen möglichen Zielkanten wird ebenfalls nicht geraten. Hypothesen werden nicht als Beobachtungen zurückgespeichert. Die Evidenz ist in SQLite persistent.

## Verwendung

Python 3.9+, keine zusätzlichen Pakete. Im Verzeichnis ausführen:

    python -m unittest -v

Einzelnes Beobachtungsbeispiel:

```python
from rrm04 import ContextCore
k = ContextCore('kira.sqlite')
a = {'nodes':{'a':'point','b':'point','c':'signal'},
     'edges':[['a','near','b'],['c','red','a']]}
b = {'nodes':a['nodes'],
     'edges':[['a','far','b'],['c','red','a']]}
for s in (a,b,a,b):
    k.observe('camera',s)
print(k.explain('camera',a,focus=0))
```

`focus=0` bezeichnet die untersuchte Kante. Ohne `focus` verweigert der Prototyp eine Entscheidung, wenn mehrere Kanten hinreichend gestützte Fortsetzungen haben. Das ist eine bewusste Einschränkung statt einer versteckten Auswahl.

## Was konkret getestet ist

16 Unit-Tests insgesamt (0.2, 0.3, 0.4): Persistenz, Regeltransfer bei neuen Knotennamen, einfache Kontexttrennung, Gleichstand, unbekannter Kontext, verweigerte Mehrfachänderungen und keine Vermischung von Dream und Beobachtung.

## Wichtige Grenzen

1. Der Kontext ist derzeit die **exakte lokale Nachbarschaft**. Es werden noch keine relevanten Kontextmerkmale aus vielen Kandidaten selbst entdeckt. Eine zusätzliche irrelevante Relation kann die Wiedererkennung verhindern.
2. Die Extraktion erfordert dieselben Knoten-IDs und dieselbe Kantenreihenfolge zwischen zwei beobachteten Zuständen. Sie akzeptiert höchstens eine Relationsänderung; bei unverändertem Zustand sammelt sie `NO_CHANGE`-Evidenz. Reale Videos benötigen vorher Tracking und Quantisierung.
3. Das Zählen von `NO_CHANGE` an mehreren Kanten kann bei automatischer Zielwahl Mehrdeutigkeiten erzeugen. `focus` ist derzeit eine explizite Fragestellung, noch keine autonome Aufmerksamkeit.
4. Das bisherige 0.3-Modul lernt zusätzlich seine unbedingten Regeln. 0.4 verwendet für `explain` ausschließlich kontextuelle Evidenz; **die beiden Modelle sind noch nicht zu einem einzigen minimalen Kern verdichtet**.
5. Das kanonische Graphverfahren aus 0.2 ist auf sieben Knoten begrenzt. Keine Laufzeitbenchmarks, keine multimodale Generierung, keine eigenständige Zielbildung, keine operationstragenden Bit-IDs.
6. `OPEN` plus eine vorformulierte Untersuchungsfrage ist **nicht** das vom Nutzer gemeinte Staunen, das mit „Was ist das überhaupt?“ beginnen kann.

## Nächster sinnvoller Schritt

**Nicht 0.5 als weiteres Modul anhängen:** Erst die gemeinsame Evidenz-/Transformationssemantik von 0.2–0.4 verdichten und die Notwendigkeit der einzelnen Grundoperationen prüfen. Anschließend ein Test, bei dem die entscheidende Kontextbedingung aus mehreren irrelevanten Merkmalen *gelernt* werden muss (Train-/Test-Trennung und echte Fehlerquote).
