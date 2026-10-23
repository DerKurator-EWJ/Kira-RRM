# RRM-RUNTIME 0.1 — Integration RRM-KERN 0.5 + RRM-ID 0.1

**Status:** ausführbarer Forschungsprototyp, **keine** vollständige binäre VM und **kein** Nachweis allgemeiner Intelligenz.

## Ausführen (Python 3.10+, nur Standardbibliothek)

```sh
python -m unittest discover -v
python benchmark.py
```

## Implementiert

- Unveränderliche, internierte Datensätze im hybriden 8-Bit-Header-/variablen Payload-Format aus `rrm_id.py`.
- Persistente SQLite-Arena: jeder Datensatz wird als BLOB gespeichert; Knoten, Relationen und Zustände referenzieren vorhandene Datensätze statt diese zu kopieren.
- Zustands-Snapshots haben stabile Referenz-Handles; isolierte Knoten bleiben erhalten.
- `observe`, `predict`, `dream` teilen die Evidenzlogik aus RRM-KERN 0.5. Reale Beobachtungen werden als **State-ID** persistiert, nicht als vollständiger JSON-Text.
- Dream erzeugt Hypothesen ohne Lernschreibzugriffe.
- Vorhersage akzeptiert direkt ein Handle eines gespeicherten Zustands.
- Reproduzierbare Paritätstests mit RRM-KERN 0.5.

## Noch nicht implementiert / Grenzen

- **Keine vollständig binäre Ausführung:** Beobachtungsabgleich, Kontextsignaturen und Regelabfrage werden weiterhin mit Python-Strukturen und JSON-kodierten Evidenzschlüsseln ausgeführt. Der Encoder/Decoder verarbeitet binäre Datensätze; der Lernalgorithmus ist nicht nativ auf Bitfeldern implementiert.
- Keine operationstragenden Instruktions-IDs, keine RRM-Schrankenarithmetik, keine selbstgewählten Ziele und keine multimodale Wahrnehmung.
- Identität durch Namen und Knotenreferenzen; keine Lösung für Objektverfolgung bei Namenswechsel über Zeit.
- Knoten-Namenspaare verwenden `KIND_RELATION` mit zwei Referenzen als **technische Zwischenform**; die finale RRM-Typsprache ist noch nicht festgelegt.
- Referenzen sind datenbanklokale SQLite-IDs, keine globalen 64-Bit-Identitäten. Der Datensatz-Header enthält den Datensatztyp, Modus und die Längenklasse, aber **keinen Opcode**.
- Das Persistenzformat ist experimentell und nicht migrationsstabil.
- SQLite-Index-, Seiten- und Verwaltungs-Overhead kann die theoretische Payload-Ersparnis übertreffen. Siehe Benchmark; **keine pauschalen Leistungsversprechen**.
- `store_state` erfordert weiterhin strukturierte Eingaben; die Grenze zur realen Bild-/Audioerkennung ist offen.

## Nächster gezielter Schritt

1. Eine **kanonische binäre Signatur** für Evidenz und Kontext statt JSON definieren.
2. Binäre Zustandsdifferenzen und Transformationen unmittelbar auf Arena-Referenzen ausführen.
3. Gegen RRM-KERN 0.5 auf identischen Daten und mit gleicher Semantik benchmarken; danach ggf. Operationscode entwerfen.

Das Ziel ist **weniger doppelte Semantik**, nicht zusätzliche parallele Lernmodule.
