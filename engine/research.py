"""
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Company Research Engine
(Merged Version)
"""

import os
import json
import glob
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_DIR = os.path.join(DATA_DIR, "nse_csv")
COMPANY_FILE = os.path.join(DATA_DIR, "companies.json")

_market_df = None

def load_companies():
    if not os.path.exists(COMPANY_FILE):
        return []
    with open(COMPANY_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def all_companies():
    return load_companies()

def get_company(code):
    for c in load_companies():
        if c["code"].upper()==code.upper():
            return c
    return None

def search_company(keyword):
    k=keyword.lower()
    return [c for c in load_companies() if k in c["name"].lower() or k in c["code"].lower() or k in c["sector"].lower() or k in c["industry"].lower()]

# ---------------- Historical Market Data ---------------- #

def load_market_data():
    df_local=pd.DataFrame()
    for file in glob.glob(os.path.join(CSV_DIR,"*.csv")):
        try:
            t=pd.read_csv(file)
            t.columns=t.columns.astype(str).str.strip().str.upper()
            req=["CODE","DATE","PREVIOUS"]
            if not all(r in t.columns for r in req):
                continue
            df_local=pd.concat([df_local,t[req]],ignore_index=True)
        except Exception:
            continue
    if not df_local.empty:
        df_local["DATE"]=pd.to_datetime(df_local["DATE"],errors="coerce")
        df_local["PREVIOUS"]=pd.to_numeric(df_local["PREVIOUS"],errors="coerce")
        df_local=df_local.dropna(subset=["CODE","DATE","PREVIOUS"]).sort_values(["CODE","DATE"]).reset_index(drop=True)
    return df_local

def get_market_data():
    global _market_df
    if _market_df is None:
        _market_df=load_market_data()
    return _market_df

def companies_by_sector(sector):
    return [c for c in load_companies() if c["sector"].lower()==sector.lower()]

def top_dividend(limit=10):
    return sorted(load_companies(),key=lambda x:x["dividend_yield"],reverse=True)[:limit]

def top_quality(limit=10):
    return sorted(load_companies(),key=lambda x:x["quality_score"],reverse=True)[:limit]

def top_roe(limit=10):
    return sorted(load_companies(),key=lambda x:x["roe"],reverse=True)[:limit]

def largest_companies(limit=10):
    return sorted(load_companies(),key=lambda x:x["market_cap"],reverse=True)[:limit]

def value_companies(limit=10):
    return sorted([c for c in load_companies() if c["pe_ratio"]>0],key=lambda x:x["pe_ratio"])[:limit]

def best_esg():
    return sorted(load_companies(),key=lambda x:x["health_score"],reverse=True)

def statistics():
    c=load_companies()
    if not c: return {}
    return {
      "companies":len(c),
      "market_cap":sum(i["market_cap"] for i in c),
      "average_dividend":round(sum(i["dividend_yield"] for i in c)/len(c),2),
      "average_roe":round(sum(i["roe"] for i in c)/len(c),2),
      "average_pe":round(sum(i["pe_ratio"] for i in c)/len(c),2),
      "average_health":round(sum(i["health_score"] for i in c)/len(c),2)
    }

def dashboard():
    return {
      "statistics":statistics(),
      "top_dividend":top_dividend(5),
      "top_quality":top_quality(5),
      "top_roe":top_roe(5),
      "largest":largest_companies(5),
      "value":value_companies(5)
    }
    # =========================================================
# 📊 DATA ENGINE
# =========================================================
df = None

def load_data():

    df_local = pd.DataFrame(columns=["Code", "Date", "Previous"])
    files = glob.glob("data/nse_csv/*.csv")

    for file in files:
        try:
            temp = pd.read_csv(file)

            # normalize columns
            temp.columns = temp.columns.astype(str).str.strip().str.upper()

            # only keep safe columns if they exist
            keep = [c for c in ["CODE", "DATE", "PREVIOUS"] if c in temp.columns]

            if len(keep) == 0:
                continue

            temp = temp[keep]

            df_local = pd.concat([df_local, temp], ignore_index=True)

        except Exception:
            continue

    # FINAL CLEANING
    if not df_local.empty:
        df_local["DATE"] = pd.to_datetime(df_local["DATE"], errors="coerce")
        df_local["PREVIOUS"] = pd.to_numeric(df_local["PREVIOUS"], errors="coerce")
        df_local = df_local.dropna()

    return df_local


def get_df():
    global df
    if df is None:
        df = load_data()
    return df
# =========================================================
# 📊 HISTORICAL MARKET STATISTICS ENGINE
# =========================================================
def estimate_market_statistics():

    df = get_df().copy()

    if df.empty:
        return None

    df.columns = df.columns.str.upper()

    df["DATE"] = pd.to_datetime(df["DATE"])

    df["PREVIOUS"] = pd.to_numeric(df["PREVIOUS"], errors="coerce")

    df = df.dropna(subset=["CODE", "DATE", "PREVIOUS"])

    df = df.sort_values(["CODE", "DATE"])

    # ------------------------------------------
    # DAILY RETURNS
    # ------------------------------------------
    df["RETURN"] = (
        df.groupby("CODE")["PREVIOUS"]
          .pct_change()
    )

    df = df.dropna()

    # ------------------------------------------
    # RETURN MATRIX
    # ------------------------------------------
    returns = df.pivot_table(
        index="DATE",
        columns="CODE",
        values="RETURN"
    )

    # remove nearly empty companies
    returns = returns.dropna(axis=1, thresh=max(20, len(returns)//4))

    returns = returns.fillna(0)

    # ------------------------------------------
    # EXPECTED RETURN
    # ------------------------------------------
    mu = returns.mean()

    # ------------------------------------------
    # VOLATILITY
    # ------------------------------------------
    sigma = returns.std()

    # ------------------------------------------
    # COVARIANCE
    # ------------------------------------------
    cov = returns.cov()

    # ------------------------------------------
    # CORRELATION
    # ------------------------------------------
    corr = returns.corr()

    return {

        "returns": returns,

        "mu": mu,

        "sigma": sigma,

        "cov": cov,

        "corr": corr

    }
# =========================================================
# 📈 CACHE MARKET STATISTICS
# =========================================================
MARKET_STATS = None


def get_market_stats():

    global MARKET_STATS

    if MARKET_STATS is None:

        MARKET_STATS = estimate_market_statistics()

    return MARKET_STATS
# =========================================================
# 🧠 MODEL → REAL COMPANY MAPPING
# =========================================================
def get_model_assets(model):

    df = get_df()

    if df is None or df.empty or "CODE" not in df.columns:
        return ASSETS.copy()

    df = df.copy()
    df["CODE"] = df["CODE"].astype(str).str.upper().str.strip()

    grouped = (
        df.groupby("CODE")["PREVIOUS"]
          .agg(["mean", "std"])
          .reset_index()
          .dropna()
    )

    grouped["return_score"] = grouped["mean"]
    grouped["risk_score"] = grouped["std"] + 1e-9
    grouped["sharpe_like"] = (
        grouped["return_score"] /
        grouped["risk_score"]
    )

    MODEL_UNIVERSES = {

        "dividend": ["EQTY", "KCB", "COOP", "EABL"],

        "growth": ["SCOM", "KQ", "NCBA", "KEGN"],

        "banking": ["EQTY", "KCB", "COOP", "NCBA"],

        "value": ["EABL", "KEGN", "SCOM", "KQ"],

        "income": ["EABL", "COOP", "KCB", "SCOM"]

    }

    allowed = MODEL_UNIVERSES.get(model, [])

    if allowed:
        grouped = grouped[grouped["CODE"].isin(allowed)]

    if grouped.empty:
        return ASSETS.copy()

    grouped["score"] = grouped["sharpe_like"]

    grouped = grouped.sort_values(
        "score",
        ascending=False
    )

    # -----------------------------
    # Company Names
    # -----------------------------
    COMPANY_NAMES = {

        "EQTY": "Equity Bank",

        "KCB": "KCB Group",

        "COOP": "Co-op Bank",

        "SCOM": "Safaricom",

        "EABL": "EABL",

        "KEGN": "KenGen",

        "NCBA": "NCBA",

        "KQ": "Kenya Airways"

    }

    assets = []

    for _, row in grouped.iterrows():

        code = row["CODE"]

        if code in COMPANY_NAMES:

            assets.append(
                (
                    COMPANY_NAMES[code],
                    code
                )
            )

    # Always return 8 assets
    for asset in ASSETS:

        if asset not in assets:

            assets.append(asset)

        if len(assets) == len(ASSETS):

            break

    return assets
# =========================================================
# 💰 DYNAMIC DIVIDEND RESEARCH ENGINE
# =========================================================
def estimate_dividend_yields(mode, model):

    MODEL_FACTOR = {

        "dividend": 1.30,
        "income":   1.20,
        "banking":  1.10,
        "value":    0.95,
        "growth":   0.70

    }

    model_factor = MODEL_FACTOR.get(model, 1.0)

    stats = get_market_stats()

    yields = {}

    for code, profile in DIVIDEND_DATABASE.items():

        y = profile["base_yield"] * model_factor

        if stats is not None:

            try:

                vol = stats["sigma"][code]

                # Stable companies deserve higher sustainable yields
                y *= max(0.80, 1.15 - (vol * 12))

            except:

                pass

        # Company stability adjustment
        y *= profile["stability"]

        # Market regime adjustment
        if mode == "bull":

            y *= 1.10

        elif mode == "bear":

            y *= 0.80

        # Realistic bounds
        y = np.clip(y, 0.00, 0.15)

        yields[code] = float(y)

    return yields
    # =========================================================
# 📈 DIVIDEND FORECAST ENGINE
# =========================================================
def forecast_dividend_yield(code, years_elapsed, mode):

    profile = DIVIDEND_DATABASE.get(code, {})

    base = DIVIDEND_BASE.get(code, 0.05)

    growth = profile.get("growth", 0.00)

    stability = profile.get("stability", 0.90)

    payout = profile.get("payout", 0.40)

    # Compound dividend growth
    forecast = base * ((1 + growth) ** years_elapsed)

    # Market regime
    if mode == "bull":
        forecast *= 1.10

    elif mode == "bear":
        forecast *= 0.80

    # Stable companies maintain dividends better
    forecast *= stability

    # Companies with higher payout ratios generally
    # distribute more income
    forecast *= (0.60 + payout)

    return float(np.clip(forecast, 0.0, 0.18))
    MODEL_UNIVERSES = {
        "dividend": [0,1,2,3,4,5,6],   # safe banks + blue chips
        "growth":   [7,5,6,1,2,3,4],   # includes KQ aggressively
        "banking":  [0,1,2,6,3],       # only banks + safaricom
        "value":    [5,6,7,4],         # cyclical + recovery stocks
        "income":   [3,4,1,0,2]        # dividend-heavy names
     }
    def company_database():

    files = glob.glob("NSE_data_all_stock_*.csv")

    names = []

    for f in files:

        try:
            temp = pd.read_csv(f)

            ...
            names.extend(...)

        except Exception:
            pass

    return sorted(set(names))
