# RRM-Minimalsprache 0.1 — vorläufige ausführbare Semantik

**Status:** technische Arbeitshypothese, keine bewiesene minimale oder universelle Sprache. Angelehnt an die RRM-Grundschrift von Erik Wilhelm Jungmann, insbesondere endliche Relationen, Zustände, offene Prozesse, rationale Schranken und die Trennung von Darstellung und Prozess.

## Grundsorten

- `U`: unterscheidbares Zeichen innerhalb einer endlichen Darstellung (keine Aussage über ein physisches Objekt).
- `R(a,typ,b)`: gerichtete, typisierte Relation zwischen zwei Zeichen.
- `S={R₁,...,Rₙ}`: endlicher Zustand mit expliziten Typzuordnungen. Mehrfachkanten sind in diesem Prototyp zulässig, ihre Identität ist noch nicht formal gelöst.
- `T(S,S')`: beobachteter Zustandsübergang, nur bei expliziter Zuordnung der Elemente.
- `∞(regel,zustand)`: **offener, fortsetzbarer Prozess**, nicht eine gespeicherte aktual unendliche Menge.
- `B(l,u)`: endliche rationale Schranke, `l≤u`; **reserviert, noch nicht implementiert**.

## Operationen (Semantik vor Bitkodierung)

1. `OBS(stream,S)`: persistiert einen beobachteten Zustand; bei vorigem Zustand wird die **beobachtete** Transformation abgeleitet. Beobachtung ist von Hypothese getrennt.
2. `DIFF(S,S')`: ergibt eine Relationstransformation oder `UNBESTIMMT`, falls Zuordnung/Änderung nicht eindeutig ist. Kein frei erfundener Vergleich inkompatibler Zustände.
3. `PROJECT(evidenz,kontext)`: liest dieselben Evidenzdatensätze entweder unter vollständigem lokalen Kontext oder als kontextfreie Aggregation. **Keine separaten Regelmodelle.**
4. `CONTINUE(S,regel)`: konstruiert einen hypothetischen Nachfolgezustand, ohne diesen als Beobachtung zu speichern.
5. `OPEN(grund)`: expliziter offener Erkenntnisstatus; **nicht** das vom Autor gemeinte „Staunen“.

Die Implementierung in `rrm05.py` ist eine **eingeschränkte ausführbare Teilmenge** dieser Sprache: Typen/Relationen, beobachtete Einzeländerungen, Evidenzprojektion und hypothetische Fortsetzung. `∞` ist bislang konzeptionell als beliebig oft erneut ausführbare Fortsetzung vorhanden, **nicht** als eigener Opcode; Schrankenarithmetik fehlt.

## Identität und ID-Entscheidung

Eine operationstragende Bit-ID wurde **absichtlich noch nicht festgelegt**. Zuerst müssen wir definieren, ob ein Bezeichner eine stabile Entität, einen unveränderlichen Wert oder eine veränderliche Prozessinstanz bezeichnet. Ein Zustandswechsel darf nicht stillschweigend die Identität verändern. Bitfelder dürfen weder die Länge beliebiger Relationen künstlich beschränken noch große Referenzen vervielfältigen. Es ist offen, ob eine feste ID mit externem Speicher, eine variable Kodierung oder eine Kombination effizienter ist.

## Nachweisgrenzen

- Lokaler Kontext wird exakt verglichen; irrelevante Merkmale verhindern Übertragung.
- `DIFF` verlangt stabile Knotennamen und Kantenreihenfolge; es erkennt keine Objekte in Videos.
- Eine Beobachtung kann mehrere Projektionen ermöglichen; sie darf nicht als unabhängige mehrfach beobachtete Evidenz gezählt werden.
- Der häufigste Ausgang ist keine Ursache und keine kalibrierte Wahrscheinlichkeit.
- Keine autonome Fragebildung, keine eigenen Ziele, kein subjektives Erleben, keine multimodale Generierung.
- Ein minimaler Satz von **Datentypen/Operationen** ist noch nicht bewiesen. Auch der Speicher- und Laufzeitaufwand ist nicht optimiert.

## Nächste falsifizierbare Prüfungen

1. Unwichtige Kontextkanten variieren; relevante Bedingungen **ohne manuelle Auswahl** lernen und auf getrennten Testfällen messen.
2. `DIFF` unabhängig von Knotennamen und Kantenreihenfolge bei kontrollierter Mehrdeutigkeit.
3. Strukturidentität vs. Prozessidentität formalisieren, erst danach Bitkodierung und Benchmarks.
4. Rationale Schranken als erste ausführbare Operationen der RRM-Prozessarithmetik hinzufügen, ohne einen universellen Verfeinerungsstopp.
