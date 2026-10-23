# RRM-KERN 0.3 — Beobachtete Transformationen verallgemeinern

**Status:** kleiner experimenteller Regelinduktor, **keine** allgemeine KI, keine Kausalitätsentdeckung, keine formale Komplettumsetzung von RRM.

## Änderung gegenüber 0.2

0.2 speicherte Übergänge zwischen *vollständigen* Graphsignaturen. 0.3 erkennt in zwei beobachteten Graphzuständen unter eng definierten Voraussetzungen eine **einzelne Änderung einer Relationsart** und abstrahiert sie als typisierte Regel:

    (Quelltyp, alte Relationsart, Zieltyp) -> neue Relationsart

Beispiel: `(point, near, point) -> far`. Diese Hypothese kann auf andere lokale IDs und auf Graphen mit zusätzlichen, unveränderten Beziehungen übertragen werden. Die Induktion verlangt eine eindeutige Regel; sie scheitert bewusst bei mehrdeutigen oder mehrschrittigen Änderungen. Bei der Anwendung muss genau **eine** Kante passen. Gleichermaßen gut gestützte konkurrierende Regeln führen zu `OPEN`.

Regeln werden ausschließlich aus beobachteten Paaren gelernt und in SQLite mit einer Evidenzanzahl gespeichert. Hypothetische Ergebnisse werden **nicht** zurück als Beobachtungen gespeichert. Standardmäßig sind zwei beobachtete Belege erforderlich, bevor eine Regel übertragen wird. Dies ist ein konfigurierbarer Prototyp-Schwellenwert, keine fundamentale RRM-Grenze.

## Test

Python 3.9+ ohne Fremdpakete:

    python -m unittest -v test_rrm.py test_rrm03.py

Beispiel:

```python
from rrm03 import RuleCore
k = RuleCore('test.sqlite')
near = {'nodes': {'a':'point','b':'point'}, 'edges': [['a','near','b']]}
far  = {'nodes': {'a':'point','b':'point'}, 'edges': [['a','far','b']]}
for s in (near,far,near,far): k.observe('camera',s)
new = {'nodes': {'x':'point','y':'point','z':'other'},
       'edges': [['x','near','y'],['z','attached','x']]}
print(k.transfer('camera',new))
```

## Präzise Grenzen

- Die Regel beschreibt **Korrelation eines beobachteten Übergangs**, nicht dessen Ursache. Zeit, Eingriffe und Kontextbedingungen sind noch nicht modelliert.
- Induktion ist auf Graphen mit höchstens sieben Knoten begrenzt, da sie mögliche Knotenzuordnungen exhaustiv prüft. Die Grenze ist rein implementierungsbedingt.
- Bei strukturellen Symmetrien können mehrere Knotenzuordnungen bestehen; nur wenn sie dieselbe abstrakte Regel ergeben, wird gelernt.
- Der Prototyp kann übergeneralisieren: Eine Regel, die in einem Kontext beobachtet wurde, ist nicht automatisch in allen anderen Kontexten gültig. Die Tests beweisen nur syntaktischen Transfer, keine semantische Richtigkeit.
- Keine eigenständige Fragebildung, keine Pixel-/Audioschnittstellen, keine operationstragenden IDs, keine RRM-Schrankenarithmetik, keine Leistungsbenchmarks.
- `rrm.py` ist der Kern aus 0.2; `rrm03.py` ist ein **getrennter Forschungsaufsatz** zur Gegenüberstellung, kein Beweis für die endgültige Architektur.

## Nächste Prüfung

Zuerst gezielte **Gegenbeispiele** und kontextabhängige Übergänge testen. Dann muss Kira entscheiden können, wann eine Regel zu allgemein ist und unter welchen Bedingungen sie gilt. Erst danach lohnt sich eine Verdichtung in eine eigene RRM-Syntax/Bit-VM. Ziel ist, Regeln aus einem gemeinsamen Mechanismus abzuleiten, nicht immer mehr Spezialmodule anzuhängen.
