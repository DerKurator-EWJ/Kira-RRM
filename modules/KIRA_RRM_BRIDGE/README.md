# KIRA RRM BRIDGE 0.1 — kontrollierte Migration

## Inhalt
- `RRM_UNIFIED_0_1/`: unveränderte Ausgangs-Runtime (Python)
- `KIRA_FOUNDATION_v0_26/`: unveränderte Foundation v0.26 (Python)
- `bridge.py`: kleine Integrationsschicht, keine neue KI-Engine
- `test_bridge.py`: vier Integrationstests

## Ausführen
Python 3.10+ ohne zusätzliche Pakete:

```bash
python -m unittest -v test_bridge
python -m unittest discover -s RRM_UNIFIED_0_1 -p 'test_unified.py' -v
python -m unittest discover -s KIRA_FOUNDATION_v0_26/tests -v
```

Die Bridge nutzt eine gemeinsame SQLite-Datei für RRM-Records, Beobachtungen, Evidenz, Identitätszuordnung, Foundation-Snapshots und InquiryQueue. Wiedererkennung und Bestand bleiben vorläufig Foundation-Algorithmen; deren Zustände werden als JSON-Snapshots in derselben Datenbank gespeichert. Es gibt **noch keine** gemeinsame binäre Evidenzsemantik für alle Foundation-Fähigkeiten. Das ist ausdrücklich eine Kompatibilitätsmigration, keine vollständige Vereinheitlichung.

### Getrennte Identitäten
`object_id` ist eine zeitübergreifende Hypothese über ein Ding; `rrm_handle` referenziert eine persistente, unveränderliche Kennung in der RRM-Arena. Ein Beobachtungs-`state_handle` ist eine andere Identität. Die IDs dürfen nicht verwechselt werden.

### Einschränkungen
- Kein direktes Android/Kotlin-Deployment, keine Kamera-/Audio-Integration.
- Foundation-Komponenten sind noch nicht auf den RRM-Kern portiert; beide Codebasen bleiben zur Regression enthalten.
- Zwei SQLite-Verbindungen (InquiryQueue und RRM) verwenden dieselbe Datei; kein gemeinsamer atomarer Commit über beide. Produktionsmigration benötigt Transaktionskoordination.
- Wiedererkennung ist ein heuristischer Zuordner, kein Identitätsbeweis; Fragen aus Bestand sind nur eine enge Form von Untersuchung, nicht das gesamte Staunen.
- Der RRM-Lernpfad verwendet weiterhin JSON-Signaturen; Bitoperationen sind nur teilweise integriert.

## Nächster gezielter Schritt
Eine **einzige** Evidenzrepräsentation für Foundation-Befunde und RRM-Transitionen spezifizieren, dann Funktionen schrittweise unter Erhalt ihrer Regressionstests portieren. Keine parallele neue Speicher-Engine einführen.
