import time
import random
import requests
import numpy as np
import pandas as pd
from tqdm import tqdm

# LISTE DER ABZUFRAGENDEN IDs
# Hier kannst du beliebige Activation Codes ergänzen, z.B. "EMSR878", "EMSR879", ...
floods = ["EMSR877"]

products_data = []   # sammelt alle Zeilen, bevor sie in einen DataFrame umgewandelt werden

# Schleife über alle Activation Codes
for flood in tqdm(floods):

    # 1. API CALL
    url = f"https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?format=json&code={flood}"
    response = requests.get(url)

    # Höfliche Pause: zufällig 5–15 Sekunden, damit der Server nicht überlastet wird
    time.sleep(random.uniform(5, 15))

    # API-Antwort in ein Python-Dictionary umwandeln
    data = response.json()

    # 2. SAFETY CHECKS
    if not isinstance(data, dict):
        print("skipping the flood:", flood, "because there is no dictionary in the api")
        continue

    if "results" not in data or not data["results"]:
        print("skipping the flood:", flood, "because the key named results is missing or the results list is empty")
        continue

    result = data["results"][0]   # Haupt-Activation-Objekt

    # 3. ACTIVATION-LEVEL FELDER (gelten für alle AOIs)
    flood_name = result.get("name", np.nan)
    flood_code = result.get("code", np.nan)
    reason = result.get("reason", np.nan)
    subcategory = result.get("subCategory", np.nan)
    activator = result.get("activator", np.nan)
    eventTime = result.get("eventTime", np.nan)
    activationTime = result.get("activationTime", np.nan)

    # 4. AOIs (Areas of Interest)
    aois = result.get("aois", [])
    if not aois:
        continue

    for aoi in aois:

        # optionale Mikropause innerhalb des AOI-Loops
        time.sleep(random.uniform(0.3, 1.2))

        aois_data_generic = {
            "flood_name": flood_name,
            "flood_code": flood_code,
            "name": aoi.get("name", np.nan),
            "number": aoi.get("number", np.nan),
            "activationCode": aoi.get("activationCode", np.nan),
            "reason": reason,
            "subcategory": subcategory,
            "activator": activator,
            "eventTime": eventTime,
            "activationTime": activationTime,
        }

        products = aoi.get("products", [])
        if not products:
            continue

        for product in products:

            # optionale Mikropause innerhalb des Product-Loops
            time.sleep(random.uniform(0.2, 0.8))

            # 5. PRODUCT-LEVEL FELDER
            aois_data_products = {
                "activation_code": product.get("activationCode", np.nan),
                "aoiName": product.get("aoiName", np.nan),
                "aoiNumber": product.get("aoiNumber", np.nan),
                "type": product.get("type", np.nan),
                "monitoring": product.get("monitoringNumber", np.nan),
                "product_polygon": product.get("extent", np.nan),
            }

            version = product.get("version")
            deliveryTime = version.get("deliveryTime", np.nan) if version else np.nan

            # 6. JSON-URLs EXTRAHIEREN
            json_urls = []
            for layer in product.get("layers", []):
                candidates = []

                if "json" in layer:
                    candidates.append(layer["json"])

                for f in layer.get("files", []):
                    candidates.extend(f.values())

                flat = []
                for c in candidates:
                    if isinstance(c, list):
                        flat.extend(c)
                    else:
                        flat.append(c)

                for item in flat:
                    if isinstance(item, dict):
                        url_item = item.get("href", "")
                    else:
                        url_item = item

                    if isinstance(url_item, str) and url_item.endswith(".json"):
                        json_urls.append(url_item)

            json_urls = list(set(json_urls))

            # 7. STATS EXTRAHIEREN (verschachtelte Struktur flach klopfen)
            stats = product.get("stats")
            if stats:
                for category, subcats in stats.items():
                    if isinstance(subcats, dict):
                        for subcat, values in subcats.items():
                            subcategory_unit = f"{category}_{subcat}_({values.get('unit', np.nan)})"
                            affected = values.get("affected", np.nan)
                            total = values.get("total", np.nan)

                            row = {
                                **aois_data_generic,
                                **aois_data_products,
                                "deliveryTime": deliveryTime,
                                "subcategory_unit": subcategory_unit,
                                "affected": affected,
                                "total": total,
                                "all_json_urls": json_urls,
                            }
                            products_data.append(row)
            else:
                row = {
                    **aois_data_generic,
                    **aois_data_products,
                    "deliveryTime": deliveryTime,
                    "subcategory_unit": np.nan,
                    "affected": np.nan,
                    "total": np.nan,
                    "all_json_urls": json_urls,
                }
                products_data.append(row)

# 8. FINALER DATAFRAME
aois_df = pd.DataFrame(products_data)
print(aois_df)
