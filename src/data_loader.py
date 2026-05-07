import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BACI_DIR = os.path.join(DATA_DIR, "raw", "BACI_HS22_V202601")

# HS product codes we care about: crude oil, refined petroleum, LNG
OIL_CODES = {2709, 2710, 2711}

# Gulf exporters whose oil transits the Strait of Hormuz
GULF = {"SAU", "IRQ", "IRN", "ARE", "KWT", "QAT", "BHR", "OMN"}

# Fraction of flow that bypasses Hormuz via overland pipeline, by (exporter, importer).
# Everything not listed defaults to 0 (fully through Hormuz).
PIPELINE_BYPASS = {
    ("SAU", "JOR"): 0.80,
    ("SAU", "EGY"): 0.40,
    ("SAU", "NLD"): 0.30, ("SAU", "GBR"): 0.30, ("SAU", "ITA"): 0.30,
    ("SAU", "ESP"): 0.30, ("SAU", "FRA"): 0.30, ("SAU", "DEU"): 0.30,
    ("SAU", "GRC"): 0.30, ("SAU", "POL"): 0.30,
    ("ARE", "CHN"): 0.50, ("ARE", "IND"): 0.50,
    ("ARE", "JPN"): 0.50, ("ARE", "KOR"): 0.50,
    ("OMN", "CHN"): 0.10, ("OMN", "IND"): 0.10,
    ("OMN", "JPN"): 0.10, ("OMN", "KOR"): 0.10,
}


def load_baci(year=2024):
    # Use cached parquet if available
    cache = os.path.join(DATA_DIR, "processed", f"baci_hs22_{year}.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)

    baci_file = os.path.join(BACI_DIR, f"BACI_HS22_Y{year}_V202601.csv")
    codes_file = os.path.join(BACI_DIR, "country_codes_V202601.csv")

    if not os.path.exists(baci_file):
        raise FileNotFoundError(f"BACI file not found: {baci_file}")

    print(f"Loading BACI {year} data (this takes a minute)...")
    df = pd.read_csv(baci_file, dtype={"k": str, "q": str}, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    df["q"] = pd.to_numeric(df["q"], errors="coerce")

    # Map numeric country codes to ISO3
    codes = pd.read_csv(codes_file)
    codes.columns = [c.lower().strip() for c in codes.columns]
    iso_col = next(c for c in codes.columns if "iso3" in c)
    code_map = dict(zip(codes["country_code"], codes[iso_col]))

    df["exporter_iso3"] = df["i"].map(code_map)
    df["importer_iso3"] = df["j"].map(code_map)
    df["hs6"] = pd.to_numeric(df["k"].str.strip(), errors="coerce").astype("Int64")
    df = df.dropna(subset=["exporter_iso3", "importer_iso3"])

    df = df[["exporter_iso3", "importer_iso3", "hs6", "q"]].rename(columns={"q": "quantity_tons"})
    df.to_parquet(cache, index=False)
    return df


def filter_oil(df):
    # Keep only oil product codes and aggregate by country pair
    mask = (pd.to_numeric(df["hs6"], errors="coerce") // 100).isin(OIL_CODES)
    flows = (df[mask]
             .groupby(["exporter_iso3", "importer_iso3"], as_index=False)["quantity_tons"]
             .sum())
    flows = flows[flows["quantity_tons"] > 0]
    flows.to_csv(os.path.join(DATA_DIR, "processed", "oil_trade_flows.csv"), index=False)
    print(f"Oil trade flows: {len(flows)} country pairs")
    return flows


def make_hormuz_shares(flows):
    # For each Gulf exporter, assign what fraction of their flow goes through Hormuz
    rows = []
    for _, r in flows[["exporter_iso3", "importer_iso3"]].drop_duplicates().iterrows():
        exp, imp = r["exporter_iso3"], r["importer_iso3"]
        if exp in GULF:
            bypass = PIPELINE_BYPASS.get((exp, imp), 0.0)
            hormuz_share = round(1.0 - bypass, 4)
        else:
            hormuz_share = 0.0
        rows.append({"exporter_iso3": exp, "importer_iso3": imp, "hormuz_share": hormuz_share})
    shares = pd.DataFrame(rows)
    shares.to_csv(os.path.join(DATA_DIR, "processed", "hormuz_shares.csv"), index=False)
    print(f"Hormuz shares assigned for {len(shares)} pairs")
    return shares


def load_price_data():
    path = os.path.join(DATA_DIR, "validation", "price_changes.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Price data not found at {path}")
    return pd.read_csv(path)
