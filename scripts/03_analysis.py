"""Names, OSM coverage against ELSTAT, and per-unit figures."""
import os, re, json, unicodedata
import numpy as np, pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
d = pd.read_csv(os.path.join(PROC, "osm_places.csv"), dtype=str).fillna("")
d["lat"], d["lon"] = d.lat.astype(float), d.lon.astype(float)
u = gpd.read_file(os.path.join(PROC, "units.geojson"))
t = pd.read_csv(os.path.join(PROC, "units.csv")).set_index("unit")

g = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326)
g = gpd.sjoin(g, u[["unit", "geometry"]], how="left", predicate="within").drop(columns="index_right")
miss = g.unit.isna()
if miss.any():
    n = gpd.sjoin_nearest(g[miss].drop(columns="unit").to_crs(2100), u[["unit", "geometry"]].to_crs(2100), how="left", max_distance=3000)
    n = n[~n.index.duplicated()]
    g.loc[n.index, "unit"] = n.unit.values
print("outside units:", g.unit.isna().sum())
g = g.dropna(subset=["unit"])
pd.DataFrame(g.drop(columns="geometry")).to_csv(os.path.join(PROC, "osm_places_units.csv"), index=False)

facts = {"n_osm": int(len(g)), "kinds": g.kind.value_counts().to_dict(), "no_name": int((g.name == "").sum())}

# ---- OSM coverage vs ELSTAT ----
c = g.pivot_table(index="unit", columns="kind", aggfunc="size", fill_value=0)
t["osm_drink"] = c.reindex(t.index).fillna(0)[["cafe", "bar", "kafeneio", "ouzeri"]].sum(axis=1)
t["osm_food"] = c.reindex(t.index).fillna(0)[["restaurant", "taverna"]].sum(axis=1)
t["osm_taverna"] = c.reindex(t.index).fillna(0)["taverna"]
t["osm_kafeneio"] = c.reindex(t.index).fillna(0)["kafeneio"]
t["cov_drink"] = t.osm_drink / t.bar2023
t["cov_food"] = t.osm_food / t.rest2023
t["cov_all"] = (t.osm_drink + t.osm_food) / (t.bar2023 + t.rest2023)
t["taverna_per10k"] = t.osm_taverna / t.pop2025 * 1e4
t.reset_index().to_csv(os.path.join(PROC, "units_full.csv"), index=False)
facts["coverage_all"] = float((t.osm_drink.sum() + t.osm_food.sum()) / (t.bar2023.sum() + t.rest2023.sum()))
facts["coverage_drink"] = float(t.osm_drink.sum() / t.bar2023.sum())
facts["coverage_food"] = float(t.osm_food.sum() / t.rest2023.sum())
pd.set_option("display.width", 200)
print(t.sort_values("cov_all")[["name", "bar2023", "rest2023", "osm_drink", "osm_food", "cov_all", "taverna_per10k"]].round(2).to_string())

# ---- names ----
def plain(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace("ς", "σ")
GENERIC = r"\b(ταβερνα|ταβερνακι|taverna|tavern|restaurant|εστιατοριο|cafe|καφε|καφετερια|bar|μπαρ|ουζερι|ouzeri|τσιπουραδικο|μεζεδοπωλειο|καφενειο|kafeneio|psistaria|ψησταρια|grill|snack|beach|&|-|\"|'|\(|\))\b"
def base(n):
    n = plain(n)
    n = re.sub(r"[\"'«»“”().,!/&+-]", " ", n)
    n = re.sub(GENERIC, " ", n)
    n = re.sub(r"^\s*(το|τα|ο|η|οι|to|ta|o|i|the)\s+", "", n.strip())
    return re.sub(r"\s+", " ", n).strip()
tav = g[g.kind.isin(["taverna", "ouzeri", "kafeneio"]) & (g.name != "")].copy()
tav["base"] = tav.name.map(base)
tav = tav[tav.base.str.len() > 1]
GR2LAT = [("ου","ou"),("αι","ai"),("ει","ei"),("οι","oi"),("μπ","b"),("ντ","d"),("γκ","g"),("τσ","ts"),("θ","th"),("χ","ch"),("ψ","ps"),("ξ","x"),
          ("α","a"),("β","v"),("γ","g"),("δ","d"),("ε","e"),("ζ","z"),("η","i"),("ι","i"),("κ","k"),("λ","l"),("μ","m"),("ν","n"),("ο","o"),("π","p"),
          ("ρ","r"),("σ","s"),("τ","t"),("υ","i"),("φ","f"),("ω","o")]
def key(b):
    for a, l in GR2LAT: b = b.replace(a, l)
    b = b.replace("h", "").replace("y", "i").replace("w", "o").replace("ph", "f")
    b = re.sub(r"(.)\1", r"\1", b)            # double letters
    return re.sub(r"(s|n)$", "", b)            # Zorbas/Zorba, Nikos/Niko
tav["base"] = tav.base.str.replace(r"\s+(το|του|tou|s)$", "", regex=True).str.strip()
tav = tav[tav.base.str.len() > 2]
tav["key"] = tav.base.map(key)
grp = tav.groupby("key").agg(n=("base", "size"), gr=("name", lambda s: next((x for x in s if re.search("[α-ωΑ-Ω]", x)), "")),
                             la=("name", lambda s: next((x for x in s if not re.search("[α-ωΑ-Ω]", x)), "")))
grp = grp.sort_values("n", ascending=False)
facts["top_names"] = [[k, int(r.n), r.gr, r.la] for k, r in grp.head(30).iterrows()]
words = tav.base.str.split().explode()
STOP = {"του", "τησ", "των", "στου", "στησ", "στο", "και", "κ", "of", "the", "and", "o", "to", "tou", "stou", "tis", "sto"}
facts["top_words"] = [[k, int(v)] for k, v in words[~words.isin(STOP)].value_counts().head(40).items()]
# owner-named places: "Του Γιώργη", "Στου Μήτσου", "Ο Μήτσος", "Η Κυρά Μαρία"
own = tav.name.map(plain).str.contains(r"^(το\s+)?(στου|στησ|του|τησ|ο|η|tou|stou|tis|o)\s+[a-zα-ω]", regex=True)
facts["owner_named_share"] = float(own.mean())
facts["owner_examples"] = tav[own].name.sample(min(25, int(own.sum())), random_state=3).tolist()
THEMES = {
    "The view (θέα, θάλασσα, ακρογιαλιά, λιμάνι)": r"θεα|θαλασσ|ακρογιαλ|λιμαν|αμμουδ|γιαλο|παραλια|thea|thalass|limani|paralia|view|sea",
    "Trees (πλάτανος, ελιά, πεύκο, κληματαριά)": r"πλατανο|ελια|πευκ|κληματ|μουρια|συκια|platano|elia|pefk|kleem",
    "Granny and family (γιαγιά, μάνα, παππούς)": r"γιαγια|μανα|παππου|θεια|μπαρμπα|yiayia|giagia|mama|pappou|barba",
    "The hangout (στέκι)": r"στεκι|steki",
    "The village and the square (χωριό, πλατεία)": r"χωριο|πλατει|horio|xorio|plateia",
    "Gods and myths": r"ζευσ|ποσειδ|αφροδιτ|απολλων|διονυσ|ερμησ|αρτεμ|αθην|zeus|poseid|aphrodit|apollo|dionys|artemis|athena|mythos|μυθοσ|olymp|ολυμπ",
}
facts["themes"] = {k: int(tav.name.map(plain).str.contains(v, regex=True).sum()) for k, v in THEMES.items()}
facts["n_named_tav"] = int(len(tav))
print(json.dumps({k: facts[k] for k in ["top_names", "themes", "owner_named_share", "coverage_all", "coverage_drink", "coverage_food"]}, ensure_ascii=False)[:3000])
print(facts["top_words"][:30]); print(facts["owner_examples"][:15])
json.dump(facts, open(os.path.join(PROC, "facts.json"), "w"), ensure_ascii=False, indent=1)
