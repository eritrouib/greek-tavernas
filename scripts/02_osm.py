"""Tavernas, kafeneia and ouzeri/tsipouradika from OpenStreetMap.

Input: an Overpass export (GeoJSON, points with tags) of every amenity=restaurant/cafe/bar/pub in Greece,
downloaded by hand from overpass-turbo.eu because the OSM servers refuse cloud connections.

OSM has no tag for "taverna" or "kafeneio", so places are classified from names and tags:
- ouzeri: ουζερί, τσιπουράδικο, μεζεδοπωλείο, ρακάδικο (names or cuisine)
- kafeneio: καφενείο / kafeneio in the name or cuisine
- taverna: ταβέρνα / taverna in the name, or a restaurant with cuisine greek / taverna / fish
- then restaurant, cafe and bar for everything else
"""
import os, re, json, unicodedata
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raw", "osm", "greece_overpass.geojson")
OUT = os.path.join(ROOT, "data", "processed", "osm_places.csv")

def plain(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("ς", "σ")

OUZERI = re.compile(r"ουζερ|ouzer|τσιπουραδ|tsipourad|μεζεδοπωλ|mezedopol|μεζεδαδ|ρακαδ|rakad|ουζαδ")
KAFENEIO = re.compile(r"καφενε|kafene|kafeni|καφενει")
TAVERNA = re.compile(r"ταβερν|taverna|tavern\b|ψαροταβερν|psarotavern|ταβερνακ")
GREEKCUI = re.compile(r"\bgreek\b|taverna|\bfish\b|seafood|\blocal\b|regional|cretan|μαγειρευτ")

rows = []
for f in json.load(open(SRC, encoding="utf-8"))["features"]:
    p = f["properties"]; lon, lat = f["geometry"]["coordinates"]
    am = p.get("amenity")
    name = (p.get("name") or p.get("name:el") or p.get("name:en") or "").strip()
    txt = plain(" ".join(str(p.get(k, "")) for k in ["name", "name:el", "name:en", "cuisine", "description", "alt_name"]))
    cui = plain(p.get("cuisine", ""))
    if OUZERI.search(txt): kind = "ouzeri"
    elif KAFENEIO.search(txt): kind = "kafeneio"
    elif TAVERNA.search(txt) or (am == "restaurant" and GREEKCUI.search(cui)): kind = "taverna"
    elif am == "restaurant": kind = "restaurant"
    elif am == "cafe": kind = "cafe"
    else: kind = "bar"
    rows.append(dict(id=p.get("@id"), amenity=am, kind=kind, name=name, name_el=p.get("name:el", ""), name_en=p.get("name:en", ""),
                     cuisine=p.get("cuisine", ""), city=p.get("addr:city", ""), lat=round(lat, 6), lon=round(lon, 6)))
d = pd.DataFrame(rows)
d.to_csv(OUT, index=False)
print(len(d), d.kind.value_counts().to_dict(), "no name:", (d.name == "").sum())
