"""
TIF-Vorschau: aus Landsat-ST_B10-Bildern eine farbige Karte machen
==================================================================

Liest alle ST_B10-TIFs aus satellite/sat_img und speichert pro Bild eine
PNG-Vorschau mit Farbskala (blau = kuehl, rot = heiss).

Damit kann man visuell pruefen, ob ein Bild brauchbar ist:
  - liegt die Stadt mittig im Bild?
  - sind grosse Bereiche bewoelkt (NoData = grau)?
  - sehen die Temperaturen physikalisch sinnvoll aus?

Aufruf:
   python satellite/tif_vorschau.py
"""

from pathlib import Path
import numpy as np
import rasterio
import matplotlib.pyplot as plt

# --- Konfiguration ----------------------------------------------------------
TIF_DIR    = Path("satellite/sat_img")
OUTPUT_DIR = Path("satellite/output/previews")
PATTERN    = "*ST_B10.TIF"

# Landsat-L2-Skalierung: DN -> Celsius
SCALE  = 0.00341802
OFFSET = 149.0
KELVIN = 273.15

# Farbskala wird auf das 2.-98. Perzentil zugeschnitten, damit einzelne
# extreme Ausreisser-Pixel (z.B. -56C Sensorartefakte) nicht die ganze
# Skala kapern und alles andere flach machen.
PERCENTIL_UNTEN = 2
PERCENTIL_OBEN  = 98


def lst_vorschau(tif_pfad: Path, out_pfad: Path):
    """Schreibt eine PNG-Vorschau eines Landsat-ST_B10-Bildes."""

    with rasterio.open(tif_pfad) as src:
        rohwerte = src.read(1)
        nodata   = src.nodata if src.nodata is not None else 0

    # In Celsius umrechnen; NoData-Pixel als NaN markieren, dann zeichnet
    # matplotlib sie automatisch transparent (bzw. in der "bad"-Farbe).
    celsius = rohwerte.astype("float32") * SCALE + OFFSET - KELVIN
    celsius[rohwerte == nodata] = np.nan

    # Farbskala-Grenzen aus den robusten Perzentilen (NaN wird ignoriert).
    vmin = np.nanpercentile(celsius, PERCENTIL_UNTEN)
    vmax = np.nanpercentile(celsius, PERCENTIL_OBEN)

    # Colormap mit grauer NoData-Farbe
    cmap = plt.get_cmap("RdYlBu_r").copy()
    cmap.set_bad(color="lightgrey")

    fig, ax = plt.subplots(figsize=(10, 10))
    bild = ax.imshow(celsius, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_axis_off()
    ax.set_title(f"{tif_pfad.name}\nOberflaechentemperatur (Celsius)", fontsize=10)

    cbar = plt.colorbar(bild, ax=ax, shrink=0.7)
    cbar.set_label("°C (Bodentemperatur)")

    plt.tight_layout()
    plt.savefig(out_pfad, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  geschrieben: {out_pfad}  ({vmin:.1f}-{vmax:.1f} C Skala)")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tifs = sorted(TIF_DIR.glob(PATTERN))
    if not tifs:
        raise FileNotFoundError(f"Keine TIFs gefunden in {TIF_DIR}")
    print(f"Gefundene TIFs: {len(tifs)}")
    for tif in tifs:
        print(f"verarbeite {tif.name} ...")
        out = OUTPUT_DIR / (tif.stem + "_vorschau.png")
        lst_vorschau(tif, out)


if __name__ == "__main__":
    main()
