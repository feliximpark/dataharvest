# Projektskizze: "Wohne ich in einer Hitzeinsel?" — Adressabfrage auf Basis von Landsat-LST

## 1. Idee und Zweck

Erweiterung der bestehenden Stadtteil-Hitzeauswertung (`heat_analysis.py`) um eine
**adressgenaue Komponente**: Eine Leserin gibt ihre Adresse ein und erfährt, ob
ihr Wohnumfeld zu den strukturell heißeren oder kühleren Bereichen Hannovers
gehört.

Journalistisch ist das die emotional packendere Variante der Hitzeinsel-Geschichte —
Leser können sich selbst verorten, statt nur auf eine abstrakte Karte zu schauen.
Daraus entsteht potenziell hohe Verweildauer und Teilbarkeit im Social Web.

## 2. Datenfluss im Konzept

1. Leser tippt Adresse ein.
2. **Geocoding** (Adresse → Längen-/Breitengrad) über Nominatim oder kommerziellen Dienst.
3. **Koordinatentransformation** vom WGS84 (EPSG:4326) ins Landsat-CRS (EPSG:32632).
4. **Pixel-Lookup**: Aus der vorberechneten Hitzekarte den Wert am Wohnort auslesen.
5. **Stadtteil-Zuordnung**: Adresse zusätzlich in das Stadtteilpolygon einordnen.
6. **Ausgabe**: Kombinierte Aussage aus Stadtteil-Wert (robust) und Adress-Umfeld-Wert (lokal).

## 3. Methodische Herausforderungen

Bevor wir das technisch umsetzen, müssen wir diese Punkte ehrlich adressieren —
sonst erzeugen wir eine **Genauigkeits-Illusion**, die journalistisch problematisch ist.

### 3.1 Auflösung: 30 × 30 Meter sind kein Haus

Ein Landsat-Pixel umfasst 900 m². Das ist nicht "die Temperatur deines Hauses",
sondern ein Mittelwert aus Dach, Hof, Garten, Straße und Nachbargrundstück. Das
muss in der Kommunikation transparent sein.

**Lösung**: Statt eines einzelnen Pixels ein **3×3- oder 5×5-Pixel-Fenster**
(90×90 m bis 150×150 m) um die Adresse auswerten und dessen Mittelwert ausgeben.
Das entspricht dem "Wohnumfeld" und glättet Sensorrauschen, ohne das räumliche
Signal zu zerstören.

### 3.2 Statistische Robustheit: Aktuell nur 2 Aufnahmen

Beim Stadtteil-Mittel werden tausende Pixel gemittelt — Wolkenschatten oder
Einzelpixel-Ausreißer verschwinden im Rauschen. Bei einer einzelnen Adresse
schlägt jeder lokale Fehler voll durch.

**Lösung**: Datenbasis erweitern. Für eine robuste Adressauskunft sollten
**10–20 wolkenfreie Sommeraufnahmen aus mehreren Jahren** zugrunde liegen. Mit
nur zwei Bildern ist der Adress-Wert ein Prototyp, kein Veröffentlichungs-Stand.

### 3.3 Kommunikation: Punktwerte verleiten zu falscher Präzision

Eine Zahl wie "2,3°C wärmer" wirkt wie ein Messwert, ist aber eine Schätzung
mit Unsicherheit. Zwei Häuser in derselben Straße könnten allein durch
Pixelrauschen unterschiedliche Werte zurückbekommen — schlecht für die
Glaubwürdigkeit.

**Lösung**: Zweistufige Ausgabe mit **robustem Stadtteilwert** im Vordergrund
und **Adress-Umfeld-Wert mit Unsicherheitsangabe** als Ergänzung. Plus eine
**kategorische Einordnung** ("Hitzeinsel ja/nein") statt einer scheingenauen
Zahl.

Beispiel-Output:

> *"Sie wohnen in **Linden-Süd**, einem Stadtteil, der im Schnitt 2,1°C
> wärmer ist als die Stadt. In Ihrer direkten Umgebung (150×150 m) liegt die
> relative Oberflächentemperatur bei etwa 2,5°C (±0,8°C), basierend auf
> X Satellitenaufnahmen. → Sie leben in einer Hitzeinsel."*

## 4. Architekturoptionen im Vergleich

| Variante | Beschreibung | Vorteile | Nachteile |
|----------|--------------|----------|-----------|
| **A) Backend-Lookup** | Python-Server hält die TIFs, nimmt Anfragen entgegen, liest Pixel pro Request. | Volle Flexibilität, Originaldaten nutzbar | Server-Kosten, Wartung, Skalierungslimit, Sicherheitsfläche |
| **B) Vorberechnete Karte** | Einmalige Berechnung der relativen LST pro Pixel als kleines GeoTIFF/PNG. Browser liest direkt. | Keine Server-Kosten, sehr schnell, einfache Wartung, beliebig skalierbar | Aufnahmedaten "eingefroren" — neue Bilder erfordern neuen Build |
| **C) Nur Stadtteilebene** | Verzicht auf Adress-Auflösung, Aussage rein auf Stadtteilbasis. | Methodisch am saubersten, einfachste Umsetzung | Geringeres Engagement, weniger packend für Leser |

**Mein Favorit ist B.** Begründung im Detail unten.

## 5. Variante B im Detail — die Architekturidee

### 5.1 Grundidee

Die Hitzeanalyse läuft **einmal lokal** auf deinem Rechner und produziert ein
**fertiges Ergebnisartefakt** — eine Karte, in der jedes Pixel den fertigen
relativen LST-Wert (gemittelt über alle Aufnahmen) enthält. Dieses Artefakt
wird in die statische Web-Auslieferung deiner Redaktion hochgeladen.

Das Web-Widget ist dann reines **JavaScript im Browser**, ohne eigenen Server:
es lädt die vorberechnete Karte, geocodet die eingegebene Adresse über einen
externen Dienst, und liest direkt im Browser den Pixelwert aus.

### 5.2 Datenformat für die Karte

Drei realistische Varianten, mit Trade-offs:

**Variante B1: Cloud-Optimized GeoTIFF (COG)**

Ein einziges GeoTIFF mit den relativen LST-Werten, optimiert für HTTP-Range-
Requests (der Browser lädt nur den Bildausschnitt, den er braucht). Auslesen
mit der Library [`georaster`](https://github.com/GeoTIFF/georaster) oder
[`geotiff.js`](https://geotiffjs.github.io/) direkt im Browser.

- Vorteil: ein Format, geo-korrekt, keine Koordinatenrechnung im Frontend nötig.
- Nachteil: GeoTIFF-Libraries im Browser sind etwa 300–800 KB JavaScript zusätzlich.

**Variante B2: PNG + JSON-Metadaten**

Die LST-Werte werden in die RGB-Kanäle eines PNG kodiert (z.B. Wert =
`(R*256 + G) / 100 - 50` ergibt Celsius-Abweichungen). Dazu eine kleine
JSON-Datei mit Bounding Box, Pixelgröße, CRS und Encoding.

- Vorteil: PNG-Decoding ist im Browser nativ, sehr klein im Code-Footprint.
- Nachteil: Koordinaten-→-Pixel-Rechnung muss selbst implementiert werden,
  Wert-Encoding/Decoding ist eine Fehlerquelle.

**Variante B3: Pre-aggregiert auf Stadtteilen + Vektor-Grid**

Wir speichern nicht jedes Landsat-Pixel, sondern aggregieren auf ein gleich-
mäßiges Hexagon- oder Quadrat-Raster (z.B. 100×100 m) und liefern das als
GeoJSON oder Vector-Tile aus.

- Vorteil: Klein, schnell, kartografisch sauber, gute Integration in Mapbox/Leaflet.
- Nachteil: Verliert die volle 30-m-Auflösung — was aber methodisch wegen
  des Wohnumfeld-Mittelungs-Arguments aus 3.1 ohnehin sinnvoll ist.

**Empfehlung**: **B3 mit 100×100 m Hex-Raster.** Das ist methodisch ehrlich
(entspricht dem "Wohnumfeld"-Konzept), technisch klein (vermutlich < 2 MB
für ganz Hannover), und in der Web-Karte sauber visualisierbar.

### 5.3 Architektur Schritt für Schritt

**Build-Phase (lokal, einmal pro Daten-Update):**

1. `heat_analysis.py` mit Erweiterung läuft durch.
2. Zusätzlich: Berechnung eines **100×100-m-Rasters** über Hannovers Stadtgebiet,
   pro Zelle wird der gemittelte relative LST-Wert berechnet.
3. Export als GeoJSON oder als Vector-Tile-Set.
4. Upload in die statische Web-Auslieferung (CDN, S3, oder das Redaktions-CMS).

**Runtime im Browser:**

1. Web-Widget lädt das GeoJSON/Vector-Tiles beim ersten Aufruf.
2. Leser tippt Adresse in ein Eingabefeld.
3. JavaScript ruft das Nominatim-API direkt vom Browser auf
   (Adresse verlässt deinen Server nie).
4. Geocoding-Ergebnis (Lon/Lat) wird auf das Hex-Raster geprojiziert.
5. Wert der Zelle, in der die Adresse liegt, wird ausgelesen.
6. Zusätzlich: Stadtteilpolygon, in dem die Adresse liegt, wird identifiziert.
7. Ergebnis-Karte zeigt: Markierung der Adresse, eingefärbte Umgebung,
   Stadtteil-Hervorhebung, Text-Erläuterung.

### 5.4 Konkrete technische Vorteile von B

- **Keine laufenden Kosten**: Statisches Hosting, kein Server, keine Wartung.
- **Beliebig skalierbar**: Egal ob 100 oder 100.000 Leser am Tag zugreifen — du
  zahlst nichts zusätzlich, weil die Last beim Browser des Lesers liegt.
- **Reproduzierbar**: Die Karte ist ein fertiges Artefakt. Wenn jemand in fünf
  Jahren fragt, was am Tag der Veröffentlichung in der Karte stand, hast du
  exakt diese Datei im Archiv.
- **DSGVO-sicher**: Adressen werden client-seitig verarbeitet und gehen nicht
  über deinen Server. Was du nicht hast, kannst du nicht verlieren.
- **Datenjournalistisch sauber**: Build-Prozess und Daten sind klar trennbar
  vom Frontend. Das Build-Skript kann veröffentlicht werden, die Auswertung
  ist reproduzierbar.

### 5.5 Konkrete technische Grenzen von B

- **Aufnahmedaten sind "eingefroren"**. Kommen neue Landsat-Bilder dazu, muss
  jemand das Build-Skript nochmal lokal ausführen und die Datei neu hochladen.
  Für ein Projekt, das vermutlich nicht wöchentlich aktualisiert wird, kein
  Problem.
- **Geocoding bleibt extern**. Nominatim hat ein freies Limit von 1 Request
  pro Sekunde, mit Pflicht-User-Agent. Für ein virales Widget wäre ein
  kommerzieller Provider (LocationIQ ~50€/Monat, MapTiler, Geoapify) nötig —
  das bleibt eine laufende Kostenposition.
- **Browser-Kompatibilität**: Vector-Tile-Rendering läuft in allen modernen
  Browsern, aber auf sehr alten Geräten kann es ruckeln. Mobile First-Tests
  sind Pflicht.

## 6. Datenschutz

Auch bei Variante B ist die Datenschutz-Lage nicht trivial:

- **Adressen sind personenbeziehbare Daten** (Art. 4 DSGVO).
- Bei direktem Browser→Nominatim-Call landen die Adressen bei der OpenStreetMap
  Foundation in Großbritannien — das muss in der Datenschutzerklärung des
  Widgets transparent gemacht werden.
- Wir speichern **nichts** persistent — die Adresse existiert nur im Browser-
  Speicher der Leserin und wird mit dem Schließen des Tabs vergessen.
- **Keine Analytics auf die eingegebenen Adressen**. Wenn ihr Klick-Statistiken
  einbaut, dann nur aggregiert (z.B. "Wie viele Leute haben das Widget genutzt"),
  niemals adress- oder stadtteilgenau.

Eine kurze, klare **Datenschutz-Erklärung im Widget selbst** ("Ihre Adresse wird
nur in Ihrem Browser verarbeitet und nicht gespeichert.") schafft Vertrauen.

## 7. Fahrplan

**Phase 1 — Hauptauswertung abschließen**

- `heat_analysis.py` mit den vorhandenen 2 Bildern laufen lassen.
- Plausibilität der Stadtteil-Ergebnisse prüfen.
- Karte als statische Visualisierung publikationsreif machen.

**Phase 2 — Datenbasis erweitern**

- Mindestens 10–20 wolkenfreie Sommeraufnahmen über Hannover beschaffen
  (Landsat 8/9 archive, ggf. ergänzt durch Sentinel-3 für niedrigere Auflösung
  aber höhere Wiederholrate).
- Für jede Aufnahme die Tageshöchsttemperatur dokumentieren (DWD, Open-Meteo).
- Aufnahmen mit Bewölkung über Hannover aussortieren.

**Phase 3 — Lokaler Prototyp Adressabfrage**

- Python-Skript, das eine Adresse als Argument nimmt, geocodet, die 3×3-Pixel-
  Nachbarschaft auswertet, den Stadtteil identifiziert und das Ergebnis in der
  Konsole ausgibt.
- Erlaubt Stabilitäts-Test: Wie unterschiedlich sind Werte zwischen Nachbar-
  adressen? Wie groß ist die Streuung über mehrere Bilder?

**Phase 4 — Build-Pipeline für Variante B**

- Erweiterung des Skripts um Export eines 100×100-m-Hex-Rasters als GeoJSON.
- Validierung: Werte im Hex-Raster vs. Stadtteil-Werte plausibel?

**Phase 5 — Web-Widget**

- HTML/CSS/JS-Implementation mit Leaflet oder Mapbox GL JS.
- Geocoding-Anbindung (zunächst Nominatim, später ggf. kommerziell).
- Iframe-Einbettung mit dynamischer Höhenanpassung (Standard-RND-Setup).
- Mobile-Tests, Performance-Tests, Datenschutz-Erklärung.

## 8. Ehrliche Gesamteinschätzung

Mit der **aktuellen Datenbasis von 2 Bildern** ist die Adress-Komponente ein
**spannender Prototyp, aber nicht veröffentlichungsreif**. Die Stadtteil-
Auswertung dagegen ist mit 2 Bildern bereits brauchbar, weil dort über
tausende Pixel gemittelt wird.

**Mit 10–20 Bildern aus mehreren Sommern** wird die Adress-Komponente eine
glaubwürdige, datenjournalistisch sehr starke Geschichte — die Sorte
Anwendung, die in Pressepreis-Diskussionen auftaucht.

Investitionsverhältnis: Phasen 1–3 sind in wenigen Tagen machbar. Phase 4–5
sind je nach Designanspruch ein bis zwei Wochen Arbeit. Der Hauptaufwand
liegt in Phase 2 (Datenbasis) und der visuellen Qualität von Phase 5.
