"""Write docs/data/*.js and copy the page."""
import os, json, shutil
import numpy as np, pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC, DOCS = os.path.join(ROOT, "data", "processed"), os.path.join(ROOT, "docs")
os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
conv = lambda o: o.item() if hasattr(o, "item") else (None if o != o else str(o))
w = lambda name, obj: open(os.path.join(DOCS, "data", name + ".js"), "w", encoding="utf-8").write(
    f"window.GR=window.GR||{{}};window.GR.{name}=" + json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=conv) + ";\n")

d = pd.read_csv(os.path.join(PROC, "osm_places_units.csv"), dtype=str).fillna("")
K = {"taverna": 0, "ouzeri": 1, "kafeneio": 2, "restaurant": 3, "cafe": 4, "bar": 5}
d["k"] = d.kind.map(K)
d = d.sort_values("k", ascending=False)   # tavernas drawn last, on top
w("points", {"lat": (d.lat.astype(float) * 1e5).round().astype(int).tolist(), "lon": (d.lon.astype(float) * 1e5).round().astype(int).tolist(),
             "k": d.k.astype(int).tolist(), "n": d.name.tolist(), "c": d.city.tolist()})

t = pd.read_csv(os.path.join(PROC, "units_full.csv")).set_index("unit")
reg = {}
u = gpd.read_file(os.path.join(PROC, "units.geojson"))
u["geometry"] = u.geometry.simplify(0.003, preserve_topology=True)
g = json.loads(u.to_json())
keep = ["name", "pop2025", "bar2016", "bar2023", "rest2016", "rest2023", "bar_per10k", "both_per10k", "bar_chg_16_23", "people_per_bar",
        "osm_drink", "osm_food", "osm_taverna", "osm_kafeneio", "cov_all", "taverna_per10k"]
for f in g["features"]:
    k = f["properties"]["unit"]; r = t.loc[k]
    f["properties"] = {"unit": k, **{c: (None if pd.isna(r[c]) else (round(float(r[c]), 4) if isinstance(r[c], (float, np.floating)) else r[c])) for c in keep}}
for f in g["features"]:
    for c in ["geometry"]:
        pass
LABEL = {"ATT": "Attica", "EL422": "Cyclades", "EL421": "Dodecanese", "EL411": "Lesvos & Limnos", "EL412": "Samos & Ikaria",
         "EL515": "Kavala & Thasos", "EL613": "Magnisia & Sporades", "EL623": "Kefalonia & Ithaca", "EL541": "Arta & Preveza",
         "EL611": "Karditsa & Trikala", "EL531": "Kozani & Grevena", "EL651": "Argolida & Arkadia", "EL653": "Messinia & Lakonia",
         "EL631": "Aitoloakarnania", "EL622": "Corfu", "EL431": "Heraklion", "EL433": "Rethymno", "EL642": "Evia", "EL632": "Achaia"}
for f in g["features"]:
    f["properties"]["label"] = LABEL.get(f["properties"]["unit"], f["properties"]["name"])
w("units", g)

nat = pd.read_csv(os.path.join(PROC, "national.csv"))
facts = json.load(open(os.path.join(PROC, "facts.json"), encoding="utf-8"))
facts["national"] = {n: {int(r.year): {"units": int(r.units), "emp": int(r.employment)} for r in nat[nat.nace == int(n)].itertuples()} for n in ["5610", "5630"]}
facts["pop2025"] = int(t.pop2025.sum())
w("facts", facts)
shutil.copy(os.path.join(ROOT, "scripts", "page_template.html"), os.path.join(DOCS, "index.html"))
for f in sorted(os.listdir(os.path.join(DOCS, "data"))):
    print(f, round(os.path.getsize(os.path.join(DOCS, "data", f)) / 1e6, 2), "MB")
