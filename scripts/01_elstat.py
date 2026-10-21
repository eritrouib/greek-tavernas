"""ELSTAT Statistical Business Register: restaurants (56.10) and bars/cafés (56.30).

National four-digit table 2011-2023 and regional-unit three-digit table 2016-2023,
plus population by regional unit (1 January 2016 and 2025).
Map units: NUTS 3 (2021) with the seven Attica units merged into one Attica.
"""
import os, re, json, glob
import pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, PROC = os.path.join(ROOT, "data", "raw"), os.path.join(ROOT, "data", "processed")

# ---- national series ----
rows = []
for f in sorted(glob.glob(os.path.join(RAW, "elstat", "nat4_*"))):
    y = int(f[-4:]); d = pd.read_excel(f, header=None).astype(object)
    for _, r in d.iterrows():
        vals = [str(v).strip() for v in r.values]
        for i, v in enumerate(vals):
            if v in ("5610", "5630") and i + 3 < len(vals):
                nums = [x for x in r.values[i + 1:] if isinstance(x, (int, float)) and not pd.isna(x)]
                if len(nums) >= 3:
                    rows.append(dict(year=y, nace=v, units=int(nums[0]), turnover_k=float(nums[1]), employment=int(nums[2])))
                break
nat = pd.DataFrame(rows).drop_duplicates(["year", "nace"]).sort_values(["nace", "year"])
nat.to_csv(os.path.join(PROC, "national.csv"), index=False)
print(nat.pivot(index="year", columns="nace", values="units"))

# ---- units: regional unit -> map unit ----
UNIT = {  # keyword in ELSTAT regional unit name -> map unit id
    "Athinon": "ATT", "Attiki": "ATT", "Pireas": "ATT", "Nissi": "ATT",
    "Evros": "EL511", "Xanthi": "EL512", "Rodopi": "EL513", "Drama": "EL514", "Kavala": "EL515", "Thassos": "EL515",
    "Imathia": "EL521", "Thessaloniki": "EL522", "Kilkis": "EL523", "Pella": "EL524", "Pieria": "EL525", "Serres": "EL526", "Chalkidiki": "EL527", "Aghio Oros": "EL527",
    "Grevena": "EL531", "Kozani": "EL531", "Kastoria": "EL532", "Florina": "EL533",
    "Arta": "EL541", "Preveza": "EL541", "Thesprotia": "EL542", "Ioannina": "EL543",
    "Karditsa": "EL611", "Trikala": "EL611", "Larissa": "EL612", "Larisa": "EL612", "Magnissia": "EL613", "Magnisia": "EL613", "Sporades": "EL613",
    "Zakynthos": "EL621", "Kerkyra": "EL622", "Ithaki": "EL623", "Kefallinia": "EL623", "Lefkada": "EL624",
    "Etoloakarnania": "EL631", "Aitoloakarnania": "EL631", "Achaia": "EL632", "Ilia": "EL633", "Ileia": "EL633",
    "Viotia": "EL641", "Voiotia": "EL641", "Evia": "EL642", "Evvoia": "EL642", "Evrytania": "EL643", "Fthiotida": "EL644", "Fokida": "EL645",
    "Argolida": "EL651", "Arkadia": "EL651", "Korinthia": "EL652", "Lakonia": "EL653", "Messinia": "EL653",
    "Lesvos": "EL411", "Limnos": "EL411", "Ikaria": "EL412", "Samos": "EL412", "Chios": "EL413",
    "Kalymnos": "EL421", "Karpathos": "EL421", "Kos": "EL421", "Rodos": "EL421", "Dodekanisos": "EL421",
    "Andros": "EL422", "Thira": "EL422", "Kea": "EL422", "Milos": "EL422", "Mykonos": "EL422", "Naxos": "EL422", "Paros": "EL422", "Syros": "EL422", "Tinos": "EL422", "Kyklades": "EL422",
    "Iraklio": "EL431", "Lassithi": "EL432", "Lasithi": "EL432", "Rethymno": "EL433", "Chania": "EL434",
}
def unit(name):
    name = str(name)
    for k, v in UNIT.items():
        if re.search(r"\b" + k + r"\b", name, re.I): return v
    return None

# ---- regional series ----
reg = []
for f in sorted(glob.glob(os.path.join(RAW, "elstat", "ru3_*"))):
    y = int(f[-4:]); d = pd.read_excel(f, header=None)
    # find the NACE code column (layout differs a little between years)
    cc = next(c for c in d.columns if d[c].astype(str).str.strip().isin(["561", "563"]).sum() > 50)
    rc = cc - 1
    d[rc] = d[rc].where(d[rc].astype(str).str.contains("Regional Unit of|Aghio|Agio", case=False, na=False)).ffill()
    d = d[d[cc].astype(str).str.strip().isin(["561", "563"])].copy()
    if d[rc].isna().any():
        # 2022: the first unit of each region has no name; units are listed in the same order every year
        print(y, "rows without a unit name:", int(d[rc].isna().sum()), "- filled from the order in 2023")
        ref = pd.read_excel(os.path.join(RAW, "elstat", "ru3_2023"), header=None)
        rcc = next(c for c in ref.columns if ref[c].astype(str).str.strip().isin(["561", "563"]).sum() > 50)
        ref[rcc - 1] = ref[rcc - 1].where(ref[rcc - 1].astype(str).str.contains("Regional Unit of|Aghio|Agio", case=False, na=False)).ffill()
        ref = ref[ref[rcc].astype(str).str.strip().isin(["561", "563"])]
        assert len(ref) == len(d)
        d[rc] = d[rc].fillna(pd.Series(ref[rcc - 1].values, index=d.index))
    for _, r in d.iterrows():
        num = lambda v: pd.to_numeric(v, errors="coerce")   # "x" = confidential
        reg.append(dict(year=y, ru=r[rc], unit=unit(r[rc]), nace=str(r[cc]).strip(), units=num(r[cc + 2]), employment=num(r[cc + 4])))
reg = pd.DataFrame(reg)
print("confidential cells:", reg.units.isna().sum(), reg[reg.units.isna()][["year", "ru", "nace"]].values.tolist()[:10])
miss = reg[reg.unit.isna()].ru.unique()
assert len(miss) == 0, miss
ru = reg.groupby(["unit", "nace", "year"]).units.sum().unstack("year")
emp = reg.groupby(["unit", "nace", "year"]).employment.sum().unstack("year")

# ---- population ----
p = pd.read_excel(os.path.join(RAW, "elstat", "pop10.xlsx"), "ΣΥΝΟΛΟ-TOTAL_2014-2025", header=None)
p = p.iloc[29:92]
p = p[p[13].astype(str).str.contains("REGIONAL UNIT|PERFECTURE|PREFECTURE", case=False) | (p[13].astype(str).str.strip() == "ATTIKI")]
p["unit"] = p[13].map(lambda s: "ATT" if str(s).strip() == "ATTIKI" else unit(re.sub(r"\d+$", "", str(s).strip()).title()))
assert p.unit.notna().all(), p[p.unit.isna()]
pop = p.groupby("unit")[[3, 12]].sum().rename(columns={3: "pop2016", 12: "pop2025"})
print("population", int(pop.pop2025.sum()))

# ---- boundaries ----
g = gpd.read_file(os.path.join(RAW, "bounds", "nutsrg_3.json"))
g = g[g.id.str.startswith("EL")].copy()
g["unit"] = g.id.where(~g.id.str.startswith("EL30"), "ATT")
names = g.groupby("unit").na.first()
names["ATT"] = "Attica"
g = g.dissolve("unit").reset_index()[["unit", "geometry"]]
g["name"] = g.unit.map(names)

t = pd.DataFrame(index=g.unit)
for nace, lab in [("561", "rest"), ("563", "bar")]:
    for y in [2016, 2019, 2020, 2023]:
        t[f"{lab}{y}"] = ru.loc[(slice(None), nace), y].droplevel(1)
    t[f"{lab}_emp2023"] = emp.loc[(slice(None), nace), 2023].droplevel(1)
t = t.join(pop)
t["bar_per10k"] = t.bar2023 / t.pop2025 * 1e4
t["rest_per10k"] = t.rest2023 / t.pop2025 * 1e4
t["both_per10k"] = (t.bar2023 + t.rest2023) / t.pop2025 * 1e4
t["bar_chg_16_23"] = t.bar2023 / t.bar2016 - 1
t["people_per_bar"] = t.pop2025 / t.bar2023
t = t.join(names.rename("name"))
t.reset_index().to_csv(os.path.join(PROC, "units.csv"), index=False)
g.merge(t.reset_index()[["unit"]], on="unit").to_file(os.path.join(PROC, "units.geojson"), driver="GeoJSON", COORDINATE_PRECISION=4)

pd.set_option("display.width", 200)
print(t.sort_values("bar_per10k", ascending=False)[["name", "bar2023", "pop2025", "bar_per10k", "both_per10k", "bar_chg_16_23"]].round(2).to_string())
print("Greece bars 2023:", int(t.bar2023.sum()), "restaurants:", int(t.rest2023.sum()), "people per bar:", round(t.pop2025.sum() / t.bar2023.sum()))
