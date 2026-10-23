# KIRA RRM CORE 0.1 — binärer Evidenzpfad

Experimenteller Integrationsstand, kein autonomes KI-System. Python 3.10+, Standardbibliothek.

## Start (Windows)

`START_TESTS.bat` ausführen oder `python -m unittest discover -p "test_*.py" -v` im Paketverzeichnis.

Separat: `cd KIRA_FOUNDATION_v0_26` und `python -m unittest discover -s tests -q`.

## Was neu ist

- `binary_learning.py`: `BinaryLearningRuntime`, erweitert die bestehende `UnifiedRuntime`.
- Beobachtete Zustände liegen als referenzierte RRM-Records im selben logischen ID-Raum.
- `DIFF` arbeitet auf binären Record-Referenzen.
- Die Lernsignatur (Endpunkttypen, Relationstyp) und der Kontext (benachbarte Relationen) werden als unveränderliche RRM-Records intern gespeichert.
- `binary_evidence` enthält ausschließlich Referenzen und Zähler statt JSON-Signaturen.
- `predict` liest diese Evidenz, überträgt eine Relationstransformation auf neue Knoten derselben Typen und liefert eine Hypothese.
- `dream` setzt Hypothesen fort; ein SQLite-Savepoint verwirft dabei alle nur spekulativ angelegten Records. Keine neuen Beobachtungen oder Evidenz.
- Die Bridge verwendet den neuen Lernpfad, FOUNDATION-Wiedererkennung/Bestand/Fragenverwaltung bleiben als kompatible Komponenten bestehen.

## Technische Grenzen

- **Keine automatische Objektzuordnung:** Zustände müssen dieselben Knotenkennungen und dieselbe Kantenreihenfolge über aufeinanderfolgende Beobachtungen besitzen. Mehr als eine veränderte Kante pro Übergang wird nicht gelernt.
- **Keine kausalen Regeln:** Häufigkeiten beobachteter Transformationen, keine Erklärung des Warum.
- **Nicht vollständig binär:** Eingabe/Ausgabe von Zuständen bleibt Python-Dictionary, Foundation-Bestand/Tracker verwenden weiterhin JSON-Snapshots. `predict` materialisiert die Ausgabe für Kompatibilität.
- **Kein autonomes Staunen:** Die bisherige Foundation-Fragenverwaltung bleibt unverändert.
- **Kein Produktionsbenchmark:** Laufzeit-/RAM-Vorteile gegenüber Foundation oder dem früheren Unified-Kern sind nicht nachgewiesen.
- **Migrationsgrenze:** Alte JSON-Evidenz (`evidence`-Tabelle) wird nicht automatisch in `binary_evidence` migriert. Eine bestehende Datenbank aus 0.1 enthält alte Evidenz, die der neue Predictor nicht berücksichtigt. Für verlässliche Migration ist ein eigener Konverter samt Abgleich notwendig. Vor Verwendung mit bestehenden Daten Backup erstellen.
- Die SQLite-Record-Handles sind lokale IDs; sie sind keine portablen, inhaltlich stabilen globalen IDs.
- Die Kontextkodierung ist eine erste experimentelle Annäherung und nicht kanonisch für alle Graphisomorphismen.
- Hypothetische `predict`-Abfragen können derzeit neue Struktur-Records internieren; `dream` rollt diese zurück. Das ist ein verbleibender Optimierungspunkt.

## Architektur

`Bridge → BinaryLearningRuntime → BinaryOps / RRM-ID → LRU-Cache → SQLite`

`FOUNDATION-Wiedererkennung / Bestand / InquiryQueue` bleiben über die Bridge angebunden, aber noch nicht vollständig auf die gemeinsame Semantik portiert.

## Teststand

- Neue Core-/Bridge-Tests: 8 bestanden.
- Unveränderte FOUNDATION-Regressionstests: 201 bestanden.
- RRM-UNIFIED-Regressionstests: 4 bestanden.

Die Tests sind keine Belege für allgemeine Intelligenz oder multimodales Lernen.
