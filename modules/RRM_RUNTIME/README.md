# RRM-RUNTIME 0.2 — direkte Operationen auf binären Referenzen

**Forschungsprototyp, keine universelle KI und keine native Maschinen-VM.**

Diese Version übernimmt den RRM-ID-Encoder und die SQLite-gestützte Arena aus Runtime 0.1 und ergänzt `binary_ops.py`:

- `RELATE`: Relation aus vorhandenen Record-Handles bilden und internieren.
- `DIFF`: Zwei Zustands-Handles anhand ihrer kodierten Knoten- und Kantenreferenzen vergleichen. Liefert geänderte Kanten, ohne komplette Zustände in Python-Dictionaries oder JSON zu materialisieren.
- `CONTINUE`: Eine beobachtete Relationsänderung auf einen Zustand übertragen; unveränderte Referenzen bleiben erhalten. Die Fortsetzung wird als neuer **hypothetischer Snapshot** gespeichert, nicht als Beobachtung oder Evidenz.

**Explizite Einschränkungen:**

1. `DIFF` setzt identische Knotenreferenzen und gleich angeordnete Kanten voraus. Automatische Objektverfolgung, Graphisomorphie und Kantenzuordnung fehlen.
2. `CONTINUE` ist eine einfache regelbasierte Substitution unter Typprüfung. Keine kausale Begründung, keine allgemeine Kontexterkennung.
3. Die Evidenzabfrage, `observe` und `predict` aus Runtime 0.1 verwenden weiterhin JSON-Signaturen. Es handelt sich **noch nicht** um einen durchgängig binären Lernpfad.
4. SQLite-Zugriffe und Python-Objekte bleiben vorhanden. „Direkt“ bedeutet hier **ohne vollständige Zustands-Dekodierung**, nicht „ohne Dekodierung irgendeines Records“.
5. Der bestehende 8-Bit-Kopf kodiert Klasse, Modus und Länge, **keinen ausführbaren Opcode**.
6. Persistenz ist durch SQLite gegeben; `CONTINUE` schreibt neue Record-Daten in den Speicher, aber keine Beobachtung. Speicherbedarf und Schreibkosten bleiben zu optimieren.

## Start

```bash
python -m unittest discover -v
python benchmark.py
```

## Nächster Schritt

Die binären Operationen in `observe`/`predict` integrieren und Evidenzsignaturen durch kanonische binäre Schlüssel ersetzen. Danach fair gegen den bisherigen JSON-Pfad benchmarken (inklusive Ingestion, Persistenz und Speicherkosten). Keine weiteren KI-Spezialmodule.
