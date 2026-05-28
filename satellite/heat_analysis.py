"""
Stadt-Hitzeanalyse mit Landsat-Satellitenbildern
================================================

Python-Portierung des R-Tutorials "Exploring Extreme Heat" (Max Donheiser).

Was macht das Skript?
  1. Liest mehrere Landsat-L2-Surface-Temperature-Bilder (.TIF, Band ST_B10).
  2. Laedt Bezirks-/Stadtgrenzen aus einem GeoPackage.
  3. Berechnet pro Bezirk die mittlere Oberflaechentemperatur (Land Surface
     Temperature = LST) - mit Coverage-Gewichtung, d.h. Pixel werden anteilig
     ihrer Ueberlappung mit dem Bezirk gewichtet (entspricht weights=TRUE in R).
  4. Berechnet pro Bild die *relative* LST je Bezirk (Abweichung vom Stadt-
     Gesamtmittel) - das ist die eigentlich interessante Groesse.
  5. Mittelt ueber alle Bilder -> langfristige Hitzekarte der Stadt.
  6. Optional: Joint Bevoelkerungsdaten aus einer Excel-Tabelle dazu.
  7. Speichert das Ergebnis als GeoJSON + CSV und zeigt eine Karte.


Welche Dateien brauchst du?
---------------------------
A) Satellitenbilder (Pflicht)
   - Ein Ordner mit ein oder mehreren Landsat L2C2 GeoTIFFs.
   - Wir brauchen das ST_B10 Band (Surface Temperature).
   - Quelle: https://earthexplorer.usgs.gov/  -> Landsat C2L2 -> ST_B10

B) Stadtgrenzen / Bezirke (Pflicht)
   - Ein GeoPackage (.gpkg) oder Shapefile mit Polygonen der einzelnen Bezirke.
   - Es muss eine Spalte mit dem Bezirksnamen geben (siehe DISTRICT_FIELD).
   - Quelle: offene Geodaten-Portale der jeweiligen Stadt
     (z.B. Bruessel: datastore.brussels, Frankfurt: offenedaten.frankfurt.de).

C) Bevoelkerungsdaten (optional - kann auf None gesetzt werden)
   - Excel-Datei mit Bevoelkerungszahl pro Bezirk.
   - Quelle: Statistisches Amt des jeweiligen Landes / der Stadt.


Einmal benoetigte Python-Pakete:
   pip install rasterio geopandas exactextract pandas openpyxl matplotlib
"""

# ============================================================
# 1. KONFIGURATION - hier alles fuer deine Stadt eintragen
# ============================================================
from pathlib import Path

# --- A) Satellitenbilder ----------------------------------------------------
# Ordner mit den Landsat-TIFs. Das Skript verarbeitet ALLE Dateien, die hier
# auf das Muster passen - leg also nur Bilder fuer dieselbe Stadt rein.
LANDSAT_DIR     = Path(r"satellite/landsat-l2c2-brussels-2025")
LANDSAT_PATTERN = "*ST_B10.TIF"   # nur Surface-Temperature-Bilder

# --- B) Stadtgrenzen / Bezirke ----------------------------------------------
BOUNDARY_FILE   = Path(r"satellite/data/UrbISAdminUnits_04000.gpkg")
BOUNDARY_LAYER  = "MonitoringDistricts"   # bei Shapefile: auf None setzen
DISTRICT_FIELD  = "NAMEDUT"               # Spalte mit dem Bezirksnamen

# --- C) Bevoelkerungsdaten (optional) ---------------------------------------
# Auf None setzen, falls du kein Bevoelkerungs-Join brauchst:
POPULATION_FILE           = Path(r"satellite/data/OPENDATA_SECTOREN_2025_NEW.xlsx")
POPULATION_CITY_FIELD     = "TX_DESCR_NL"            # Spalte mit Stadtname
POPULATION_CITY_VALUE     = "Brussel"                # auf welche Stadt filtern
POPULATION_DISTRICT_FIELD = "TX_DESCR_SECTOR_NL"     # Bezirks-Spalte (Join-Key)
POPULATION_VALUE_FIELD    = "TOTAL"                  # Spalte mit der Einwohnerzahl

# --- Ergebnis ---------------------------------------------------------------
OUTPUT_DIR      = Path(r"satellite/output")

# --- Landsat-L2-Skalierung: DN -> Kelvin -> Celsius -------------------------
# Quelle: https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products
LANDSAT_SCALE  = 0.00341802
LANDSAT_OFFSET = 149.0
KELVIN_ZERO_C  = 273.15


# ============================================================
# 2. IMPORTS
# ============================================================
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
from exactextract import exact_extract
import matplotlib.pyplot as plt


# ============================================================
# 3. KERN-FUNKTIONEN
# ============================================================
def dn_to_celsius(value):
    """
    Wandelt einen Landsat-Rohwert (Digital Number) in Grad Celsius um.
    Die Formel ist linear, deshalb kann man sie sowohl auf Einzelpixel als
    auch auf bereits gemittelte Werte anwenden - das Ergebnis ist identisch.
    """
    return value * LANDSAT_SCALE + LANDSAT_OFFSET - KELVIN_ZERO_C


def align_crs(vector_gdf, raster_path):
    """
    Projiziert das Vector-Layer ins CRS des Rasters um, falls noetig.
    Ohne diesen Schritt liegen Pixel und Polygone an unterschiedlichen Orten
    und alle weiteren Berechnungen sind Quatsch.
    """
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
    if vector_gdf.crs != raster_crs:
        return vector_gdf.to_crs(raster_crs)
    return vector_gdf


def global_mean_celsius(raster_path, city_polygon):
    """
    Mittelwert der LST ueber das gesamte Stadtgebiet (alle Bezirke vereint).
    Entspricht in R: global(landsat, fun=mean, na.rm=TRUE) nach dem Maskieren.
    """
    with rasterio.open(raster_path) as src:
        # crop=True schneidet auf die Polygon-Extent zu, filled=False liefert
        # ein MaskedArray, das die NoData-Pixel beim Mittel automatisch ignoriert.
        masked, _ = rio_mask(src, [city_polygon], crop=True, filled=False)
    return dn_to_celsius(float(masked.mean()))


def relative_lst_per_district(raster_path, districts):
    """
    Berechnet fuer ein Landsat-Bild pro Bezirk die *relative* LST in Celsius
    (Abweichung vom Stadt-Gesamtmittel).

    Verwendet exact_extract mit Coverage-Gewichtung: jeder Pixel wird mit dem
    Anteil seiner Flaeche innerhalb des Bezirks gewichtet. Das ist besonders
    wichtig bei kleinen Bezirken, wo schon 1-2 Randpixel das Ergebnis kippen
    koennen (entspricht dem R-Argument weights=TRUE in terra::extract).
    """
    districts = align_crs(districts, raster_path)

    # Stadtgesamtflaeche fuers Referenzmittel
    city = districts.geometry.union_all() if hasattr(districts.geometry, "union_all") \
           else districts.geometry.unary_union
    city_mean = global_mean_celsius(raster_path, city)

    # Bezirks-Mittelwerte (Coverage-gewichtet)
    stats = exact_extract(
        rast=str(raster_path),
        vec=districts,
        ops=["mean"],
        output="pandas",
    )
    district_celsius = dn_to_celsius(stats["mean"])

    # Abweichung vom Stadt-Mittel
    return (district_celsius - city_mean).to_numpy()


def load_population(districts):
    """
    Optionaler Schritt: Bevoelkerung pro Bezirk aus einer Excel-Datei einlesen
    und an das districts-GeoDataFrame anjoinen.
    Gibt das (ggf. erweiterte) GeoDataFrame zurueck.
    """
    if POPULATION_FILE is None or not POPULATION_FILE.exists():
        print("Keine Bevoelkerungsdaten konfiguriert oder Datei nicht gefunden - ueberspringe.")
        return districts

    print(f"Lade Bevoelkerungsdaten aus {POPULATION_FILE} ...")
    pop = pd.read_excel(POPULATION_FILE)
    pop = pop[pop[POPULATION_CITY_FIELD] == POPULATION_CITY_VALUE]
    pop = pop[[POPULATION_DISTRICT_FIELD, POPULATION_VALUE_FIELD]].rename(
        columns={
            POPULATION_DISTRICT_FIELD: DISTRICT_FIELD,
            POPULATION_VALUE_FIELD: "pop",
        }
    )
    return districts.merge(pop, on=DISTRICT_FIELD, how="left")


# ============================================================
# 4. PIPELINE
# ============================================================
def main():
    # --- Bezirke laden ------------------------------------------------------
    print(f"Lade Bezirksgrenzen aus {BOUNDARY_FILE} ...")
    districts = gpd.read_file(BOUNDARY_FILE, layer=BOUNDARY_LAYER) \
                if BOUNDARY_LAYER else gpd.read_file(BOUNDARY_FILE)
    print(f"  -> {len(districts)} Bezirke, CRS: {districts.crs}")

    # --- Bilder finden ------------------------------------------------------
    images = sorted(LANDSAT_DIR.glob(LANDSAT_PATTERN))
    if not images:
        raise FileNotFoundError(
            f"Keine Dateien gefunden mit Muster '{LANDSAT_PATTERN}' in {LANDSAT_DIR}"
        )
    print(f"Gefundene Satellitenbilder: {len(images)}")

    # --- Pro Bild: relative LST pro Bezirk ---------------------------------
    rel_per_image = {}
    for img in images:
        print(f"  verarbeite {img.name} ...")
        rel_per_image[img.stem] = relative_lst_per_district(img, districts)

    # --- Ueber alle Bilder mitteln -----------------------------------------
    rel_df = pd.DataFrame(rel_per_image)
    districts["mean_rel_lst"] = rel_df.mean(axis=1).to_numpy()

    # --- Optional: Bevoelkerung anjoinen ------------------------------------
    districts = load_population(districts)

    # --- Outputs schreiben --------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    geojson_path = OUTPUT_DIR / "districts_heat.geojson"
    csv_path     = OUTPUT_DIR / "districts_heat.csv"
    districts.to_file(geojson_path, driver="GeoJSON")
    districts.drop(columns="geometry").to_csv(csv_path, index=False)
    print(f"Geschrieben: {geojson_path}")
    print(f"Geschrieben: {csv_path}")

    # --- Karte plotten ------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    districts.plot(
        column="mean_rel_lst",
        cmap="RdYlBu_r",         # rot = heisser, blau = kuehler
        legend=True,
        ax=ax,
        edgecolor="white",
        linewidth=0.2,
        legend_kwds={"label": "Abweichung vom Stadtmittel (Celsius)"},
    )
    ax.set_title("Durchschnittliche relative Oberflaechentemperatur je Bezirk")
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "heat_map.png", dpi=150)
    plt.show()

    # --- Kurze Zusammenfassung in der Konsole ------------------------------
    cols = [DISTRICT_FIELD, "mean_rel_lst"]
    if "pop" in districts.columns:
        cols.append("pop")
    print("\nTop 3 heisseste Bezirke:")
    print(districts.nlargest(3, "mean_rel_lst")[cols].to_string(index=False))
    print("\nTop 3 kuehlste Bezirke:")
    print(districts.nsmallest(3, "mean_rel_lst")[cols].to_string(index=False))

    return districts


if __name__ == "__main__":
    main()
