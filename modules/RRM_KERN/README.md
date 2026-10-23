# RRM-KERN 0.2 — Formale Minimalgrammatik und relationaler Prototyp

**Status:** überprüfbarer Versuch, **keine** allgemeine KI und **keine** vollständige Formalisierung der RRM. Die ursprüngliche Sequenzversion 0.1 liegt als `legacy_sequence.py` bei; 0.2 ist eine zusätzliche **alternative Kernhypothese**, keine weitere Feature-Schicht.

## Minimale ausführbare Sprache (Arbeitsdefinition)

```
Knoten := (lokale_ID, Typ)
Relation := (Quell_ID, Relationsart, Ziel_ID)
Zustand := (endliche Knotenmenge, endliche Relationsmultimenge)
Beobachtung := (Stream, Position, Zustand)
Übergang := (Zustand_t, Zustand_t+1, Evidenzanzahl)
Offene_Frage := (Zustand, Frage, OPEN)
Fortsetzung := bestgestützter beobachteter Übergang | OPEN
```

**Semantik:** IDs sind innerhalb eines Zustands bloße lokale Referenzen. Strukturelle Identität wird durch die gleiche gerichtete, typisierte Graphstruktur **bis auf Umbenennung** definiert. Die exakte Kanonisierung erhält Richtung, Typ und Multiplizität der Kanten. Beobachtungen bleiben unverändert in SQLite; Übergänge werden als Evidenz gezählt. Vorhersage ist die häufigste beobachtete Fortsetzung des aktuellen Strukturzustands, nicht logische Gewissheit. Dream setzt dieselben Übergänge hypothetisch fort und verändert die Evidenz nicht. Eine Frage ist explizit gestellt; **OPEN ist nicht Staunen**. Das System formuliert noch keine eigenen Fragen.

## Minimaler Test

Im Verzeichnis mit Python 3.9+:

    python -m unittest -v test_rrm.py

Oder interaktiv:

```python
from rrm import RelationalCore
k = RelationalCore('versuch.sqlite')
a = {'nodes': {'a':'punkt','b':'punkt'}, 'edges': [['a','nahe','b']]}
b = {'nodes': {'x':'punkt','y':'punkt'}, 'edges': [['x','fern','y']]}
for state in [a,b,a,b,a]: k.observe('versuch',state)
print(k.predict('versuch'))
print(k.dream('versuch',3))
print(k.ask('versuch',a,'Warum verändert sich die Relation?'))
```

## Nachweis und Grenzen

- **Getestet:** identische Struktur trotz anderer Knotennamen; Persistenz; beobachtete Strukturübergänge; hypothetische Fortsetzung ohne Rückkopplung; explizite offene Fragen; Isolation verschiedener Streams.
- **Noch nicht erreicht:** freie Erkennung von Relationen aus Pixeln/Ton, allgemeine kausale Regelbildung, Verallgemeinerung von Strukturänderungen auf neue Ausgangsgraphen, autonome Fragenauswahl, RRM-Schrankenarithmetik, operationstragende Bit-IDs, Echtzeit, Video-/Tonausgabe.
- **Bewusste Grenze:** exakte kanonische Graphrepräsentation maximal sieben Knoten. Oberhalb davon wird abgebrochen statt stillschweigend eine ungenaue Gleichsetzung vorzunehmen. Die Kanonisierung ist kombinatorisch teuer; kein Effizienznachweis.
- **Offener Prozess (∞):** fortsetzbare endliche Beobachtungsfolge, keine real unendliche Berechnung. Die Grenze von sieben Knoten ist **eine temporäre Implementierungsgrenze**, kein ontologisches RRM-Axiom.
- **Achtung:** Aus der Beobachtung A→B folgt noch keine kausale Erklärung *warum* B folgt. Wiedererkennen ist nicht Verstehen.

## Nächster echter Forschungsentscheid

Nicht weitere Features anhängen. Zunächst messen, ob diese Graphstruktur gegenüber 0.1 **neue** Relationen abstrahiert, und ob sich eine *Transformationsregel* (welche Relation ändert sich?) aus mehreren Beispielen lernen lässt, ohne sie für jedes Beispiel zu programmieren. Anschließend mit den Kotlin-Kernstrukturen des ursprünglichen Kira-Systems vergleichen. Die Bit-ID-Grammatik wird erst nach der Semantik festgelegt.
