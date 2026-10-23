# RRM-KERN 0.1 — Minimaler ausführbarer Versuchsaufbau

**Status:** Experimenteller, begrenzter Sequenzlerner. Kein allgemeines KI-Modell, kein vollständiger RRM-Interpreter, keine Android-App. Keine Behauptung, dass hier Bewusstsein, echtes Staunen, multimodales Lernen oder Videoerzeugung implementiert seien.

## Bezug zur RRM
- Beobachtungen: endliche unterscheidbare Zeichen in geordneter Folge.
- Relationen: endliche Kontexte -> beobachtete mögliche Fortsetzungen.
- Stabilisierung: wiederholte Evidenz wird gezählt, nicht als absolute Wahrheit ausgegeben.
- Offener Prozess (∞): es gibt keinen fest definierten letzten Lernschritt. Jede Ausführung bleibt endlich, und das System kann nach Neustart fortsetzen. Dies implementiert **nicht** die vollständige RRM-Schrankenarithmetik.
- Hypothese vs. Beobachtung: generierte Sequenzen verändern die Evidenz nicht.
- Staunen: noch **nicht** implementiert. Ein offener Status ist lediglich eine unbeantwortete Vorhersagefrage und darf nicht mit deinem Staunen gleichgesetzt werden.

## Ausführen (Windows, Python 3.9+)
Im Ordner Terminal öffnen:

    python kern.py observe A B C A B C A B
    python kern.py predict
    python kern.py dream --steps 8
    python kern.py audit
    python kern.py history
    python -m unittest -v test_kern.py

Daten bleiben in `kern.sqlite` auch nach Programmende bestehen. Mit `--stream name` sind mehrere getrennte Versuchsreihen möglich; `--db datei.sqlite` wählt die Datenbank.

## Exakte Semantik
Für den aktuellen Kontext wird das längste Suffix (maximal 6 Zeichen) gesucht, das bereits vor einer beobachteten Fortsetzung vorkam. Alle beobachteten Nachfolger dieses Kontextes werden gezählt. Der häufigste wird als Hypothese zurückgegeben, bei Gleichstand lexikographisch. Ist kein Kontext belegt, bleibt der Status OPEN. `certainty` ist **nur** die relative Häufigkeit innerhalb der gefundenen Beobachtungen, keine kalibrierte Wahrscheinlichkeit. `dream` wendet dieselbe Regel iterativ an und schreibt seine Ergebnisse nicht in den Erfahrungsspeicher. `audit` misst lediglich die Trefferquote bei den tatsächlich abgegebenen Online-Vorhersagen.

## Warum das noch nicht der Heilige Gral ist
Das Programm ist ein bewusst einfaches Suffix-/Kontextmodell. Es entdeckt keine beliebigen Gesetzmäßigkeiten, keine multimodalen semantischen Relationen, keine Ziele und keine eigenen Fragen im Sinne des Staunens. Die Eingabe ist bereits symbolisiert. Der Kern kann lange Abhängigkeiten außerhalb seiner Kontexttiefe nicht erkennen. Die Speicherung ist nicht informationsverlustfrei komprimiert; Rohereignisse werden vollständig bewahrt. Die ID-Bitgrammatik ist absichtlich **nicht** erfunden worden: Der bestehende Android-`EquinoxId64.kt` verwendet BLAKE2b-IDs; eine neue operationstragende Kodierung muss gegen die Originalimplementierung spezifiziert und getestet werden.

## Prüfbare nächste Entscheidung
Eine RRM-Minimalsprache definieren: endliche Zeichen, Relation, Zustandsänderung, offene Fortsetzung, Evidenzstatus und Identität. Anschließend prüfen, ob die vorhandenen Kotlin-Makros dieselbe Semantik bereits abdecken, und das experimentelle Modell durch einen **modalitätsunabhängigen** relationalen Lernmechanismus ersetzen. Kein weiterer Funktionszuwachs ohne Test der gemeinsamen Semantik.
