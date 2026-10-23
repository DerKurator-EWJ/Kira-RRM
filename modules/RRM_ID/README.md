# RRM-ID 0.1 — hybride Bitarchitektur C

**Experimenteller Wire-Format-Prototyp, keine fertige Kira-Runtime.** Baut auf den Begriffen von RRM-KERN 0.5 auf, integriert sich aber noch nicht automatisch in dessen SQLite-Lernkern.

## Format

1 Byte Kopf: `KKK MM LLL` (3 Bit Sorte, 2 Bit Modus, 3 Bit Längenklasse).

- Sorten 0–5: Knoten, Relation, Zustand, Übergang, Prozess, Schranke; 6–7 reserviert.
- Modi 0: unmittelbarer Bitwert, 1: externer Referenzwert, 2: Referenzliste, 3: reserviert.
- Längenklassen 0–6: 0, 1, 3, 7, 13, 37, 64 Bit; Klasse 7: tatsächliche Bitlänge als ULEB128.
- Nutzdaten: auf Byte gerundete, little-endian bitgepackte Darstellung; überzählige Bits müssen null sein. Logische Werte dürfen z. B. 13, 37, 73 oder 137 Bit haben.
- Referenzlisten: ULEB128-Anzahl gefolgt von ULEB128-Handles. Kein willkürliches starres 64-Bit-Limit für Referenzen.

## Identitäten

`Arena` vergibt stabile lokale Handles an unveränderliche Datensätze und dedupliziert identische Bytes. Eine Relation speichert Referenzen auf Quellknoten, Relationsart und Zielknoten. `ProcessTable` vergibt eine **eigene stabile Prozess-ID**, deren aktueller Snapshot sich verändern kann. **Wichtig:** Die Wire-IDs sind keine global eindeutigen oder kryptografisch abgesicherten Identitäten. Die Indizes (`offsets`, `intern`) haben zusätzlichen RAM-Bedarf, der im Bytebenchmark nicht enthalten ist.

## Ausführen

```
python -m unittest discover -s . -p 'test_*.py' -v
python benchmark.py
```

## Grenzen und offene Designfragen

- Header-Bitaufteilung und Längenklassen sind **experimentelle Kandidaten**, keine aus RRM-Axiomen abgeleitete optimale Lösung.
- Der Kopf beschreibt Datensorte und Speicherform, **noch keine allgemeine ausführbare Operation**. Eine Operationsgrammatik mit verifizierbarer Semantik fehlt.
- Die binäre Referenzliste hat keine automatische Rollen-/Typsicherung oder Persistenz der Arena. Nicht vertrauenswürdige Daten müssen zusätzlich begrenzt werden.
- `Arena` ist append-only, in-memory und für einen einzelnen Prozess. Kein GC, keine Transaktionen, keine Thread-Sicherheit, kein Reopen und keine Speicherabbildung.
- Bitpacking spart Bytes auf Datenträgern, muss aber gegen CPU-Kosten und Index-Overhead gemessen werden. `benchmark.py` vergleicht nur Payloadgrößen gegen 64-Bit-Slots und misst **keine vergleichbaren Laufzeiten** beider Implementierungen.
- Es gibt keine künstliche fundamentale Verfeinerungsgrenze für RRM-∞; das Dateiformat setzt aber technische Größen- und Ressourcenlimits.
- Noch kein multimodales Lernen, keine eigene Fragebildung, kein autonomer Generationsmechanismus.

## Nächster Schritt

Reale RRM-0.5-Beobachtungen in die Arena überführen; ein typisiertes Operationsformat mit `OBS`, `DIFF`, `PROJECT`, `CONTINUE`, `OPEN` definieren; dann gegen 64-Bit-Slots und Python-Objekte **inklusive Indizes** mit denselben Workloads benchmarken. Danach erst über die endgültige Headerbelegung entscheiden.
