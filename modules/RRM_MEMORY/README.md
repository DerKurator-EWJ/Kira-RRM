# RRM-MEMORY 0.1 — drei Speicherstrategien im Vergleich

Dies ist ein **isolierter Benchmark-Prototyp**, keine Integration in Kiras produktive Runtime. Er verwendet die tatsächliche `Record`-Kodierung aus `RRM_RUNTIME_0_2/rrm_id.py` (benötigt die benachbarte Originaldatei) und prüft drei physische Ablagestrategien bei unveränderter logischer Handle-Identität.

## Strategien

- **RAM**: alle kodierten Records in einem Python-Dictionary; keine Datenbankzugriffe während des Messlaufs.
- **Disk**: jeder Zugriff über SQLite-`SELECT` auf dieselbe Datei; SQLite und das Betriebssystem cachen intern trotzdem Seiten.
- **Routed Cache**: SQLite mit `kind`-Index für Routing, plus LRU-Cache für Nutzdaten mit festem Bytebudget. Der Index ist eine technische Strukturklasse, **kein gelerntes Makro-Routing**.

## Ausführung

Aus dem übergeordneten Verzeichnis, in dem `RRM_RUNTIME_0_2/` und `RRM_MEMORY_0_1/` nebeneinander liegen:

```bash
cd RRM_MEMORY_0_1
python -m unittest -v test_memory.py
python benchmark.py
```

## Ergebnisse eines lokalen Durchlaufs

12.000 binäre RRM-Records, je 10.000 Abrufe, Cachebudget 65.536 Nutzdatenbytes. Ein identischer Decode und eine identische Prüfsumme für alle drei Backends; Zeiten sind **einzelne Python-Messläufe**, keine belastbare Hardware-Rangliste.

| Zugriffsmuster | RAM | SQLite | LRU + SQLite |
|---|---:|---:|---:|
| 90 % aus 128 häufigen Handles | 12,2 ms | 53,0 ms | 19,2 ms |
| Gleichverteilt aus 12.000 Handles | 14,1 ms | 54,4 ms | 46,4 ms |

- Hot: LRU 8.959/10.000 Treffer, 1.041 SQLite-Abrufe, 8.130 Byte Nutzdaten im Cache.
- Gleichverteilt: LRU 3.295/10.000 Treffer, 6.705 SQLite-Abrufe, 52.198 Byte Nutzdaten im Cache.
- Routing für 4.000 Datensätze einer Klasse: RAM-Scan ca. 0,6 ms; SQLite-Scan ca. 4 ms; SQLite-Index ca. 1,1 ms.
- Reine Wire-Nutzdaten aller Records: 93.853 Byte. SQLite-Datei: 323.584 Byte, einschließlich Seiten und Index. Python-Dictionary-Overhead wurde **nicht** gemessen.

## Interpretation und Grenzen

- Vollständiger RAM-Zugriff ist in diesem kleinen, bereits initialisierten Test am schnellsten. Der Cache spart bei lokaler Wiederverwendung erheblich Datenbankzugriffe, ist aber nicht generell schneller als RAM.
- **Kein echter SSD-vs-RAM-Benchmark**: SQLite-Seiten und Dateiinhalt können im Betriebssystem-Page-Cache liegen. Weder physische I/O-Zahlen noch GPU/VRAM, Energie, Latenzverteilung, konkurrierende Lasten oder Kaltstartzeiten wurden gemessen.
- Die Cachegrenze betrifft nur die **Payloadbytes**; Python-Objekte, LRU-Metadaten und SQLite-Cache benötigen weiteren RAM. Es gibt keine Speicherbudget-Garantie für den gesamten Prozess.
- Die Datensätze sind synthetisch, die Zugriffe simuliert. Noch kein echter Kira-Workload, keine multimodale Last, kein trainiertes Makro-Routing.
- Alle Backends benutzen stabile integer Handles; Speicherort ist **kein Teil der Identität**.

## Nächster technischer Schritt

`BinaryOps` aus `RRM_RUNTIME_0_2` gegen ein einheitliches `get/put/route`-Backend ausführen und echte Kira-Workloads instrumentieren. Danach RAM-High-Water-Mark, Cache-Miss-Latenzen, SSD-Reads, Batch-I/O und Prefetching messen. Kein neuer KI-Mechanismus erforderlich.
