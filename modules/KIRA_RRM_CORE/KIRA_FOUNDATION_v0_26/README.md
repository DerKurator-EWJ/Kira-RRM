# KIRA FOUNDATION v0.26 – Identität und Staunen

Neue Brücke `foundation/identitaetsfragen.py`: erkennt mehrdeutige Zuordnungen zwischen Sichten und bekannten Dingkennungen und hinterlegt dazu Fragen in der bestehenden SQLite-Fragenverwaltung. Werden spätere Beobachtungen eindeutig, wird die Frage vorläufig geklärt. Die bisherige Wiedererkennung bleibt unverändert. Keine Videoanalyse, kein semantischer Identitätsbeweis.

**Windows:** `START_IDENTITAET.bat` für die Demonstration, `TEST_ALL.bat` für die gesamte Testsuite. Python 3 erforderlich.

**Begriffe:** Sicht (einmalige Beobachtung), Ding (vorläufig wiedererkannte Einheit), Identitätsfrage (ungeklärte Zuordnung), Staunen (Verwaltung der Frage). Die Wortbrücke in `begriffe.json` enthält die englische technische Entsprechung.

**Grenze:** Kandidatenbewertung nutzt weiterhin einfache Merkmals- und Lageabstände. Bei zwei konkurrierenden Sichten ist die Frage konservativ offen; der bestehende Tracker kann dennoch eine vorläufige Kennung vergeben. Keine automatischen Experimente zur Auflösung der Frage.
