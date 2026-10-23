# Kiras Begriffe – die Wortbrücke

Die **deutschen Namen** sind die Begriffe, mit denen wir Kira erklären und planen. Die **englischen technischen Bezeichnungen** sind eine verbindliche Hilfe für künftige Entwickler und Sprachmodelle, wenn sie Code schreiben.

Die maschinenlesbare Liste liegt in `begriffe.json`. `foundation/wortbruecke.py` kann Namen in beide Richtungen nachschlagen. Beispiel: `technisch("Staunen") == "Inquiry"`.

**Wichtig:** Das Register übersetzt **keine Python-Syntax** und ersetzt keinen Compiler. Die Programmiersprache bleibt korrektes Python; bestehende öffentliche Schnittstellen werden nicht automatisch umbenannt. Neue Dokumentation und Anzeigen sollen bevorzugt die deutschen Namen benutzen. Bei neuen Funktionen kann die technische Bezeichnung aus dem Register als konsistentes Muster dienen.

| Kiras Name | Technische Bezeichnung |
|---|---|
| Spur | `Observation` |
| Merkmalsmaß | `FeatureQuantizer` |
| Zusammenhang | `Relation` |
| Band | `Group` |
| Blicktiefe | `AdaptiveResolution` |
| Wiedererkennung | `IdentityTracker` |
| Bestand | `PartWholeModel` |
| Staunen | `Inquiry` |
| Erwartung | `Prediction` |
| Vermutung | `Hypothesis` |
| Beleg | `Evidence` |
| Festigung | `Consolidation` |
| Umbau | `Revision` |
| Gedächtnis | `Memory` |
| Blickmaß | `AttentionBudget` |
| Prüfung | `Evaluation` |
| Ding | `Entity` |

- **Identitätsfrage** – Ist eine Sicht einem bereits bekannten Ding zuzuordnen? (IdentityInquiry)
