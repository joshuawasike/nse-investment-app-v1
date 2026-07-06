from datetime import datetime 
from flask import Flask, render_template, request, redirect, session
import pandas as pd
import numpy as np
import glob
import matplotlib
import json
import os
import io
import base64
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "jobura_secure_secure_v3"
@app.route("/companies")
def companies():

    files = glob.glob("NSE_data_all_stock_*.csv")

    if not files:
        return "No CSV files found"

    names = []

    for f in files:
        try:
            temp = pd.read_csv(f)

            # normalize column names
            temp.columns = temp.columns.astype(str).str.strip().str.upper()

            # possible name columns (VERY IMPORTANT FIX)
            possible_cols = ["NAME", "COMPANY", "SECURITY", "SYMBOL", "STOCK", "ISSUER"]

            name_col = None
            for col in temp.columns:
                if col in possible_cols:
                    name_col = col
                    break

            if name_col is None:
                continue

            names.extend(
                temp[name_col]
                .dropna()
                .astype(str)
                .str.upper()
                .str.strip()
                .tolist()
            )

        except Exception:
            continue

    if not names:
        return "No valid company names found"

    return "<br>".join(sorted(set(names)))
# =========================================================
# 🔐 CONFIG
# =========================================================
ADMIN_PASSWORD = "Jobura@542542"
DB_FILE = "users.json"

# =========================================================
# 📦 SAFE USER SYSTEM
# =========================================================
def load_users():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)
        return []

    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        return [u for u in data if isinstance(u, dict)]

    except:
        return []


def save_users(users):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except:
        pass


def is_active(user):
    return (
        isinstance(user, dict)
        and "status" in user
        and (
            "monthly" in user.get("status", "")
            or "yearly" in user.get("status", "")
        )
    )

# =========================================================
# 💳 PAYMENT INFO
# =========================================================
PAYMENT_INFO = {
    "paybill": "542542",
    "account_number": "31909",
    "account_name": "Jobura Solutions"
}

# =========================================================
# 💰 PRICING CONFIG (ADD THIS HERE)
# =========================================================
PRICING = {
    "monthly": 400,
    "yearly": 4000
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
# 🧠 MODEL → REAL COMPANY MAPPING (FIXED SAFE VERSION)
# =========================================================
def get_model_assets(model):

    df = get_df()

    if df is None or df.empty or "CODE" not in df.columns:
        return ASSETS[:8]

    df = df.copy()
    df["CODE"] = df["CODE"].astype(str).str.upper().str.strip()

    grouped = df.groupby("CODE")["PREVIOUS"].agg(["mean", "std"]).reset_index()
    grouped = grouped.dropna()

    grouped["return_score"] = grouped["mean"]
    grouped["risk_score"] = grouped["std"] + 1e-9
    grouped["sharpe_like"] = grouped["return_score"] / grouped["risk_score"]

    MODEL_UNIVERSES = {
        "dividend": ["EQTY", "KCB", "COOP", "EABL"],
        "growth":   ["SCOM", "KQ", "NCBA", "KEGN"],
        "banking":  ["EQTY", "KCB", "COOP", "NCBA"],
        "value":    ["EABL", "KEGN", "SCOM", "KQ"],
        "income":   ["EABL", "COOP", "KCB", "SCOM"]
    }

    allowed = MODEL_UNIVERSES.get(model, [])

    if allowed:
        grouped = grouped[grouped["CODE"].isin(allowed)]

    if grouped.empty:
        grouped = df.groupby("CODE")["PREVIOUS"].agg(["mean", "std"]).reset_index()
        grouped["return_score"] = grouped["mean"]
        grouped["risk_score"] = grouped["std"] + 1e-9
        grouped["sharpe_like"] = grouped["return_score"] / grouped["risk_score"]

    def bias(code):
        return 1.2 if code in allowed else 1.0

    grouped["score"] = grouped["CODE"].apply(bias) * grouped["sharpe_like"]

    grouped = grouped.sort_values("score", ascending=False).head(len(ASSETS))

    # IMPORTANT: keep SAME structure as ASSETS (8 slots always)
    # -----------------------------------------------------
# Company code -> company name
# -----------------------------------------------------
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

assets = [

    (
        COMPANY_NAMES.get(row["CODE"], row["CODE"]),
        row["CODE"]
    )

    for _, row in grouped.iterrows()

]

    # PAD to 8 to prevent broadcast errors
    while len(assets) < len(ASSETS):
        assets.append(ASSETS[len(assets)])

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
# 📊 ASSETS
# =========================================================
ASSETS = [
    ("Equity Bank","EQTY"),
    ("KCB Group","KCB"),
    ("Co-op Bank","COOP"),
    ("Safaricom","SCOM"),
    ("EABL","EABL"),
    ("KenGen","KEGN"),
    ("NCBA","NCBA"),
    ("Kenya Airways","KQ")
]

N = len(ASSETS)
# =========================================================
# 💰 INSTITUTIONAL DIVIDEND RESEARCH DATABASE
# =========================================================
DIVIDEND_DATABASE = {

    "EQTY":{
        "months":[6],
        "base_yield":0.090,
        "growth":0.060,
        "payout":0.45,
        "stability":0.96,
        "quality":0.95,
        "policy":"progressive",
        "sector":"Banking"
    },

    "KCB":{
        "months":[5,11],
        "base_yield":0.085,
        "growth":0.055,
        "payout":0.42,
        "stability":0.94,
        "quality":0.93,
        "policy":"progressive",
        "sector":"Banking"
    },

    "COOP":{
        "months":[6],
        "base_yield":0.090,
        "growth":0.070,
        "payout":0.50,
        "stability":0.98,
        "quality":0.96,
        "policy":"stable",
        "sector":"Banking"
    },

    "SCOM":{
        "months":[4,10],
        "base_yield":0.065,
        "growth":0.080,
        "payout":0.70,
        "stability":0.99,
        "quality":0.98,
        "policy":"progressive",
        "sector":"Telecom"
    },

    "EABL":{
        "months":[7],
        "base_yield":0.075,
        "growth":0.040,
        "payout":0.65,
        "stability":0.95,
        "quality":0.92,
        "policy":"stable",
        "sector":"Consumer"
    },

    "KEGN":{
        "months":[8],
        "base_yield":0.080,
        "growth":0.050,
        "payout":0.55,
        "stability":0.90,
        "quality":0.88,
        "policy":"cyclical",
        "sector":"Utilities"
    },

    "NCBA":{
        "months":[5,11],
        "base_yield":0.060,
        "growth":0.050,
        "payout":0.40,
        "stability":0.93,
        "quality":0.90,
        "policy":"progressive",
        "sector":"Banking"
    },

    "KQ":{
        "months":[],
        "base_yield":0.000,
        "growth":0.000,
        "payout":0.00,
        "stability":0.20,
        "quality":0.25,
        "policy":"suspended",
        "sector":"Airline"
    }

}
# =========================================================
# 💰 DYNAMIC DIVIDEND ENGINE
# =========================================================

DIVIDEND_BASE = {

    "EQTY":0.090,
    "KCB":0.085,
    "COOP":0.090,
    "SCOM":0.065,
    "EABL":0.075,
    "KEGN":0.080,
    "NCBA":0.060,
    "KQ":0.000

}


def estimate_dividend_yields(mode, model):
    MODEL_FACTOR = {

        "dividend":1.30,

        "income":1.20,

        "banking":1.10,

        "value":0.95,

        "growth":0.70

    }

    model_factor = MODEL_FACTOR.get(model, 1.0)

    stats = get_market_stats()

    yields = {}

    for code, base in DIVIDEND_BASE.items():

        y = base * model_factor

        if stats is not None:

            try:

                vol = stats["sigma"][code]

                # Stable companies generally sustain dividends better
                y *= max(0.80, 1.15 - (vol * 12))

            except:

                pass

        # Market regime adjustments
        if mode == "bull":

            y *= 1.10

        elif mode == "bear":

            y *= 0.80

        # Keep within realistic limits
        y = np.clip(y, 0.00, 0.15)

        yields[code] = float(y)

    return yields
    # =========================================================
    # 📈 DIVIDEND FORECAST ENGINE
    # =========================================================
    def forecast_dividend_yield(code, years_elapsed, mode):

        profile = DIVIDEND_DATABASE.get(code)

        if profile is None:
            return 0.0

        base = profile["base_yield"]
        growth = profile["growth"]
        quality = profile["quality"]
        policy = profile["policy"]

        # compound dividend growth
        forecast = base * ((1 + growth) ** years_elapsed)

        # market regime
        if mode == "bull":
            forecast *= 1.08

        elif mode == "bear":
            forecast *= 0.82

        # dividend policy
        if policy == "progressive":
            forecast *= 1.05

        elif policy == "stable":
            forecast *= 1.00

        elif policy == "cyclical":
            forecast *= 0.92

        elif policy == "suspended":
            forecast = 0.0

        # company quality
        forecast *= quality

        return float(np.clip(forecast, 0.0, 0.18))
# =========================================================
# 🧠 AI ENGINE
# =========================================================
def optimize_weights(sim, mode="normal"):

    n = sim.shape[0]

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9
    downside = np.mean(np.minimum(sim, 0), axis=1)

    # =========================================================
    # RISK PARITY
    # =========================================================
    inv_vol = 1.0 / vol
    rp_weights = inv_vol / np.sum(inv_vol)

    # =========================================================
    # ALPHA SCORE (SAFE DYNAMIC VERSION)
    # =========================================================
    safe_ratio = mean / (vol + 1e-9)
    score = safe_ratio - (1.1 * np.abs(downside))

    # NO FIXED INDEXING LIKE score[7]
    alpha = np.tanh(score * 2.0)
    alpha_weights = np.exp(alpha - np.max(alpha))
    alpha_weights = alpha_weights / np.sum(alpha_weights)

    # =========================================================
    # HYBRID
    # =========================================================
    w = 0.55 * rp_weights + 0.45 * alpha_weights

    # =========================================================
    # REGIME TILT (SAFE)
    # =========================================================
    if mode == "bull":
        w *= 1.05
    elif mode == "bear":
        w *= 0.95

    # =========================================================
    # NORMALIZATION
    # =========================================================
    w = np.maximum(w, 1e-6)
    w = w / np.sum(w)

    # =========================================================
    # DYNAMIC CLIP (NO FIXED SIZE ARRAYS)
    # =========================================================
    MIN = np.full(n, 0.03)
    MAX = np.full(n, 0.40)

    w = np.clip(w, MIN, MAX)
    w = w / np.sum(w)

    return w
# =========================================================
# 🎯 APPLY MODEL BIAS TO WEIGHTS
# =========================================================
def apply_model_bias(weights, model):

    w = np.array(weights, dtype=float)

    if len(w) < 8:
        return w / np.sum(w)

    # =====================================================
    # DIVIDEND MODEL
    # =====================================================
    if model == "dividend":

        target = np.array([
            0.20,  # EQTY
            0.18,  # KCB
            0.15,  # COOP
            0.10,  # SCOM
            0.15,  # EABL
            0.12,  # KEGN
            0.08,  # NCBA
            0.02   # KQ
        ])

    # =====================================================
    # GROWTH MODEL
    # =====================================================
    elif model == "growth":

        target = np.array([
            0.08,
            0.08,
            0.08,
            0.25,
            0.08,
            0.08,
            0.10,
            0.25
        ])

    # =====================================================
    # BANKING MODEL
    # =====================================================
    elif model == "banking":

        target = np.array([
            0.25,
            0.22,
            0.20,
            0.05,
            0.05,
            0.05,
            0.15,
            0.03
        ])

    # =====================================================
    # VALUE MODEL
    # =====================================================
    elif model == "value":

        target = np.array([
            0.08,
            0.08,
            0.08,
            0.05,
            0.12,
            0.20,
            0.12,
            0.27
        ])

    # =====================================================
    # INCOME MODEL
    # =====================================================
    elif model == "income":

        target = np.array([
            0.10,
            0.15,
            0.15,
            0.10,
            0.25,
            0.15,
            0.08,
            0.02
        ])

    else:
        target = np.ones(len(w))

    # blend optimizer with model identity
    w = (0.30 * w) + (0.70 * target)

    w = w / np.sum(w)

    return w
    
MODEL_UNIVERSES = {
    "dividend": [0,1,2,3,4,5,6],   # safe banks + blue chips
    "growth":   [7,5,6,1,2,3,4],   # includes KQ aggressively
    "banking":  [0,1,2,6,3],       # only banks + safaricom
    "value":    [5,6,7,4],         # cyclical + recovery stocks
    "income":   [3,4,1,0,2]        # dividend-heavy names
}
# =========================================================
# 🏦 DIVIDEND HEALTH ENGINE
# =========================================================
def dividend_health_score(code, stats):

    profile = DIVIDEND_DATABASE.get(code, {})

    stability = profile.get("stability", 0.90)
    quality = profile.get("quality", 0.90)

    if stats is None:
        return float(np.clip(
            0.60 * stability + 0.40 * quality,
            0.20,
            0.99
        ))

    try:

        mu = float(stats["mu"][code])
        sigma = float(stats["sigma"][code])

        score = (
            0.35 * stability +
            0.35 * quality +
            0.20 * np.clip(mu * 30, 0, 1) +
            0.10 * np.clip(1 - sigma * 20, 0, 1)
        )

        return float(np.clip(score, 0.20, 0.99))

    except:

        return float(np.clip(
            0.60 * stability + 0.40 * quality,
            0.20,
            0.99
        ))
# =========================================================
# 🌍 ECONOMIC REGIME ENGINE
# =========================================================

ECONOMIC_REGIMES = {

    "normal":{

        "drift":1.00,
        "vol":1.00,

        "sector":{

            "Banking":1.00,
            "Telecom":1.00,
            "Consumer":1.00,
            "Utilities":1.00,
            "Airline":1.00

        }

    },

    "bull":{

        "drift":1.25,
        "vol":0.85,

        "sector":{

            "Banking":1.30,
            "Telecom":1.10,
            "Consumer":1.15,
            "Utilities":0.95,
            "Airline":1.60

        }

    },

    "bear":{

        "drift":0.60,
        "vol":1.45,

        "sector":{

            "Banking":0.70,
            "Telecom":0.95,
            "Consumer":0.80,
            "Utilities":1.05,
            "Airline":0.25

        }

    }

}
# =========================================================
# 🌍 INSTITUTIONAL MARKET GENERATOR V12
# Historical NSE Monte Carlo Engine
# =========================================================
def generate_market(mode, N, drift, vol, momentum):

    stats = get_market_stats()

    periods = 300

    # -----------------------------------------------------
    # FALLBACK IF NO HISTORICAL DATA
    # -----------------------------------------------------
    if stats is None:

        return np.random.normal(
            drift,
            vol,
            (N, periods)
        )

    # -----------------------------------------------------
    # HISTORICAL PARAMETERS
    # -----------------------------------------------------
    mu = stats["mu"].copy()
    sigma = stats["sigma"].copy()
    cov = stats["cov"].copy()

    # -----------------------------------------------------
    # MATCH OUR NSE UNIVERSE
    # -----------------------------------------------------
    codes = [asset[1] for asset in ASSETS]

    available = [
        c for c in codes
        if c in mu.index
        and c in cov.index
    ]

    if len(available) < 2:

        return np.random.normal(
            drift,
            vol,
            (N, periods)
        )

    mu = mu.loc[available]
    sector_multiplier = []

    regime = ECONOMIC_REGIMES.get(
        mode,
        ECONOMIC_REGIMES["normal"]
    )

    for code in available:

        profile = DIVIDEND_DATABASE.get(code, {})

        sector = profile.get("sector","Banking")

        sector_multiplier.append(

            regime["sector"].get(
                sector,
                1.0
            )

        )

    sector_multiplier = np.array(sector_multiplier)

    mu *= sector_multiplier
    sigma = sigma.loc[available]
    cov = cov.loc[available, available]

    # -----------------------------------------------------
    # REGIME ADJUSTMENTS
    # -----------------------------------------------------
    regime = ECONOMIC_REGIMES.get(
        mode,
        ECONOMIC_REGIMES["normal"]
    )

    mu *= regime["drift"]

    cov *= regime["vol"]

    # -----------------------------------------------------
    # POSITIVE DEFINITE COVARIANCE
    # -----------------------------------------------------
    cov += np.eye(len(cov)) * 1e-8

    try:

        L = np.linalg.cholesky(cov)

    except np.linalg.LinAlgError:

        eigvals, eigvecs = np.linalg.eigh(cov)

        eigvals[eigvals < 1e-8] = 1e-8

        cov = eigvecs @ np.diag(eigvals) @ eigvecs.T

        L = np.linalg.cholesky(cov)

    # -----------------------------------------------------
    # FAT TAIL SHOCKS
    # -----------------------------------------------------
    shocks = np.random.standard_t(
        df=6,
        size=(len(mu), periods)
    )

    correlated = L @ shocks

    # -----------------------------------------------------
    # MOMENTUM PROCESS
    # -----------------------------------------------------
    trend = np.zeros_like(correlated)

    phi = min(0.95, max(0.10, momentum))

    for t in range(1, periods):

        trend[:, t] = (
            phi * trend[:, t - 1]
            + correlated[:, t]
        )

    # -----------------------------------------------------
    # EXPECTED RETURNS
    # -----------------------------------------------------
    R = mu.values[:, None] + trend

    # -----------------------------------------------------
    # VOLATILITY SCALING
    # -----------------------------------------------------
    scale = sigma.values[:, None]

    R *= (scale / np.std(R, axis=1, keepdims=True))

    # -----------------------------------------------------
    # SAFETY LIMITS
    # -----------------------------------------------------
    R = np.clip(
        R,
        -0.12,
        0.15
    )

    # -----------------------------------------------------
    # PAD IF NECESSARY
    # -----------------------------------------------------
    if len(mu) < N:

        extra = np.random.normal(
            drift,
            vol,
            (N - len(mu), periods)
        )

        R = np.vstack([R, extra])

    return R[:N]
# =========================================================
# 🧠 AI PORTFOLIO ADVISOR (ADD HERE)
# =========================================================
def ai_portfolio_advisor(weights, R, assets):

    avg_returns = np.mean(R, axis=1)
    risk = np.std(avg_returns)

    top_idx = int(np.argmax(weights))
    top_asset = assets[top_idx][0]

    if risk < 0.01:
        comment = "Low risk environment. Defensive portfolio."
    elif risk < 0.02:
        comment = "Moderate risk. Balanced exposure."
    else:
        comment = "High volatility. Consider reducing risk."

    return {
        "top_asset": top_asset,
        "risk_level": float(risk),
        "commentary": comment
    }
# =========================================================
# 🏦 INSTITUTIONAL ALLOCATOR V4
# =========================================================
def institutional_allocator(sim, mode):

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9

    sharpe = mean / vol

    score = sharpe.copy()

    # =====================================================
    # REGIME TILTS
    # =====================================================
    if mode == "bull":
        score = score * 1.25 + mean * 15

    elif mode == "bear":
        score = score * 0.70 - vol * 4

    else:
        score = score * 1.00

    # =====================================================
    # SOFTMAX WEIGHTS
    # =====================================================
    score = score - np.max(score)

    weights = np.exp(score)
    weights = weights / np.sum(weights)

    # =====================================================
    # CONCENTRATION LIMITS
    # =====================================================
    weights = np.clip(weights, 0.05, 0.35)
    weights = weights / np.sum(weights)

    return weights
# =========================================================
# 🧠 PATH SIMULATION (MISSING FUNCTION FIX)
# =========================================================
def simulate_paths(R, mode):

    REGIME = {
        "normal": {"mu": 0.0025, "vol": 1.0},
        "bull":   {"mu": 0.0055, "vol": 1.2},
        "bear":   {"mu": -0.0035, "vol": 1.3},
    }

    cfg = REGIME.get(mode, REGIME["normal"])
    N = R.shape[0]
    T = R.shape[1]

    sim = []

    for i in range(N):
        base_vol = np.std(R[i]) + 1e-9
        series = []

        for t in range(T):
            shock = np.random.standard_t(5) * base_vol * cfg["vol"]
            step = R[i][t] + cfg["mu"] + shock

            if mode == "bear":
                step = np.clip(step, -0.05, 0.01)

            series.append(step)

        sim.append(series)

    return np.array(sim)
# =========================================================
# 📈 FULL INSTITUTIONAL SIMULATION ENGINE V11
# =========================================================
def simulate(monthly, years, mode, model="dividend"):

    # -----------------------------------------------------
    # MODEL CONFIGURATION
    # -----------------------------------------------------
    MODEL_PARAMS = {
        "dividend": (0.0035, 0.012, 0.60),
        "growth":   (0.0060, 0.022, 1.10),
        "banking":  (0.0045, 0.016, 0.80),
        "value":    (0.0040, 0.015, 0.75),
        "income":   (0.0038, 0.013, 0.70),
    }

    drift, vol, momentum = MODEL_PARAMS.get(
        model,
        MODEL_PARAMS["dividend"]
    )

    # -----------------------------------------------------
    # MARKET
    # -----------------------------------------------------
    R_full = generate_market(
        mode,
        len(ASSETS),
        drift,
        vol,
        momentum
    )

    # -----------------------------------------------------
    # SELECT MODEL ASSETS
    # -----------------------------------------------------
    assets = get_model_assets(model)

    names = [a[0] for a in ASSETS]
    selected = [a[0] for a in assets]

    idx = [
        names.index(n)
        for n in selected
        if n in names
    ]

    if len(idx) == 0:
        idx = list(range(len(ASSETS)))
        assets = ASSETS

    R = R_full[idx]

    # -----------------------------------------------------
    # PORTFOLIO WEIGHTS
    # -----------------------------------------------------
    weights = institutional_allocator(R, mode)
    weights = apply_model_bias(weights, model)

    if len(weights) > len(assets):
        weights = weights[:len(assets)]
        weights = weights / np.sum(weights)

    # -----------------------------------------------------
    # SIMULATION SETTINGS
    # -----------------------------------------------------
    months = years * 12

    invested = monthly * months

    nav = 0.0

    curve = []

    dividends = np.zeros(len(weights))

    yield_table = estimate_dividend_yields(mode, model)
    stats = get_market_stats()

    yields = np.array([

        yield_table.get(asset[1],0.05)

        for asset in assets

    ])
    capital = np.zeros(len(weights))

    # -----------------------------------------------------
    # REGIME DIVIDEND MULTIPLIER
    # -----------------------------------------------------
    regime_multiplier = {
        "normal": 1.00,
        "bull": 1.15,
        "bear": 0.85
    }.get(mode, 1.0)

    # -----------------------------------------------------
    # MONTHLY LOOP
    # -----------------------------------------------------
    for m in range(months):

        col = m % R.shape[1]

        # yearly rebalance
        if m > 0 and m % 12 == 0:

            weights = institutional_allocator(R, mode)
            weights = apply_model_bias(weights, model)

            if len(weights) > len(assets):
                weights = weights[:len(assets)]

            weights = weights / np.sum(weights)

        portfolio_return = np.dot(weights, R[:, col])

        if mode == "bull":
            portfolio_return = np.clip(portfolio_return, -0.03, 0.08)

        elif mode == "bear":
            portfolio_return = np.clip(portfolio_return, -0.05, 0.03)

        else:
            portfolio_return = np.clip(portfolio_return, -0.04, 0.05)

        nav *= (1 + portfolio_return)

        nav += monthly

        curve.append(nav)

        # Monthly contribution
        monthly_alloc = monthly * weights

        # Add new investment
        capital += monthly_alloc

        # Grow each asset using its own return
        asset_returns = R[:, col]

        capital *= (1 + asset_returns)
        current_month = (m % 12) + 1


        # -----------------------------------------------------
        # DIVIDEND PAYMENT ENGINE
        # -----------------------------------------------------
        current_month = (m % 12) + 1

        for i, asset in enumerate(assets):

            code = asset[1]

            profile = DIVIDEND_DATABASE.get(code, {})

            payment_months = profile.get("months", [])

            growth = profile.get("growth", 0.00)

            stability = profile.get("stability", 1.00)

            payout = profile.get("payout", 0.00)

            # Only pay dividends in scheduled months
            if current_month in payment_months:

                # Dividend yield grows over time
                current_yield = forecast_dividend_yield(
                    code,
                    m // 12,
                    mode
                )

                # Market regime adjustments
                if mode == "bull":
                    current_yield *= 1.10

                elif mode == "bear":
                    current_yield *= 0.80

                # Company may reduce or skip dividend
                health = dividend_health_score(code, stats)

                annual_dividend = (

                    capital[i]

                    * current_yield

                    * payout

                    * health

                )

                dividend = annual_dividend / max(len(payment_months), 1)

                dividends[i] += dividend
    # -----------------------------------------------------
    # FINAL VALUES
    # -----------------------------------------------------
    final_nav = curve[-1]

    total_dividends = float(dividends.sum())

    portfolio_value = float(final_nav + total_dividends)

    curve_np = np.array(curve)

    monthly_returns = np.diff(curve_np) / np.maximum(curve_np[:-1], 1)

    annual_return = (portfolio_value / invested) ** (1 / years) - 1

    cagr = annual_return

    volatility = np.std(monthly_returns) * np.sqrt(12)

    sharpe = (
        annual_return - 0.05
    ) / max(volatility, 1e-9)

    running_max = np.maximum.accumulate(curve_np)

    drawdown = (curve_np - running_max) / running_max

    max_drawdown = abs(np.min(drawdown))

    inflation = 0.05

    real_value = portfolio_value / ((1 + inflation) ** years)

    # -----------------------------------------------------
    # BREAKDOWN
    # -----------------------------------------------------
    monthly_alloc = monthly * weights

    breakdown = []

    asset_values = capital + dividends

    for i in range(len(assets)):

        invested_asset = invested * weights[i]

        breakdown.append({

            "asset": assets[i][0],

            "allocation_pct": round(weights[i] * 100, 2),

            # Amount actually invested into this asset
            "capital": round(float(invested_asset), 2),

            # Current value after growth
            "current_value": round(float(capital[i]), 2),

            # Profit excluding dividends
            "capital_gain": round(float(capital[i] - invested_asset), 2),

            # Total dividends earned
            "dividends": round(float(dividends[i]), 2),

            # Final value including dividends
            "total_return": round(float(asset_values[i]), 2)

        })
    # -----------------------------------------------------
    # PLAN
    # -----------------------------------------------------
    plan = []

    for i in range(len(assets)):

        plan.append({

            "name":
                assets[i][0],

            "percent":
                round(weights[i] * 100, 2),

            "kes":
                round(monthly_alloc[i], 2)

        })
        returns_table = []

        for i in range(len(assets)):

            invested_asset = invested * weights[i]

            returns_table.append({

                "asset": assets[i][0],

                "capital": round(invested_asset,2),

                "value": round(float(capital[i]),2),

                "gain": round(float(capital[i]-invested_asset),2),

                "dividends": round(float(dividends[i]),2),

                "total": round(float(capital[i]+dividends[i]),2),

                "annual_return": round(
                    annual_return*100,
                    2
                )

            })
    # -----------------------------------------------------
    # AI
    # -----------------------------------------------------
    ai = ai_portfolio_advisor(
        weights,
        R,
        assets
    )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------
    summary = {

        "invested": round(float(invested),2),

        "value": round(float(portfolio_value),2),

        "real_value": round(float(real_value),2),

        "dividends": round(total_dividends,2),

        "annual_return": round(annual_return*100,2),

        "cagr": round(cagr*100,2),

        "volatility": round(volatility*100,2),

        "sharpe": round(sharpe,2),

        "max_drawdown": round(max_drawdown*100,2)

    }

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------
    return {

        "summary": summary,

        "chart": chart(curve),

        "plan": plan,

        "curve": curve,

        "ai": ai,

        "assets": breakdown,
        
        "returns": returns_table
    }
# =========================================================
# 📊 CHART
# =========================================================
def chart(curve):
    fig, ax = plt.subplots(figsize=(10, 5))

    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    x = np.arange(len(curve))
    y = np.array(curve)

    ax.plot(x, y, color="#60a5fa", linewidth=2)
    ax.fill_between(x, y, color="#60a5fa", alpha=0.15)

    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#334155")
    ax.spines["left"].set_color("#334155")
    ax.spines["top"].set_color("#0b0f19")
    ax.spines["right"].set_color("#0b0f19")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)

    plt.close(fig)

    return base64.b64encode(buf.read()).decode()

# =========================================================
# 🔐 LOGIN
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password"

    return """
    <form method="POST" style="padding:20px;">
        <input name="password" type="password" placeholder="Admin Password">
        <button type="submit">Login</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# =========================================================
# 🎯 GOAL PLANNER
# =========================================================
def years_to_goal(monthly, target, annual_return=0.10):

    if monthly <= 0 or target <= 0:
        return None

    monthly_rate = annual_return / 12

    balance = 0
    months = 0

    while balance < target and months < 1200:
        balance = balance * (1 + monthly_rate) + monthly
        months += 1

    return round(months / 12, 1)


def monthly_for_goal(target, years, annual_return=0.10):

    if target <= 0 or years <= 0:
        return None

    r = annual_return / 12
    n = years * 12

    factor = ((1 + r) ** n - 1) / r

    monthly = target / factor

    return round(monthly, 0)
# =========================================================
# 🌐 MAIN ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()
    is_premium = False
    data = {}
    goal_result = None
    best_model_name = None
    best_model_value = 0
    ranking = []

    try:

        if request.method == "POST":

            # INPUTS
            monthly = float(request.form.get("monthly") or 0)
            years = int(request.form.get("years") or 1)
            target_amount = float(request.form.get("target_amount") or 0)

            # GOAL ANALYSIS
            if target_amount > 0:
                goal_result = {
                    "target": target_amount,
                    "current_monthly": monthly,
                    "years_needed": years_to_goal(monthly, target_amount),
                    "monthly_5": monthly_for_goal(target_amount, 5),
                    "monthly_10": monthly_for_goal(target_amount, 10),
                    "monthly_15": monthly_for_goal(target_amount, 15)
                }

            # USER CHECK
            code = request.form.get("transaction_code", "").strip().upper()
            phone = request.form.get("phone", "").strip()

            for u in users:
                if u.get("code") == code and is_active(u):
                    is_premium = True

            # RUN ALL MODELS
            models = [
                "dividend",
                "growth",
                "banking",
                "value",
                "income"
            ]

            for m in models:

                normal = simulate(monthly, years, "normal", m)

                if is_premium:
                    bull = simulate(monthly, years, "bull", m)
                    bear = simulate(monthly, years, "bear", m)
                else:
                    bull = None
                    bear = None

                data[m] = {
                    "normal": normal,
                    "bull": bull,
                    "bear": bear
                }

            # SAVE NEW USER
            if code and not any(u.get("code") == code for u in users):

                users.append({
                    "code": code,
                    "phone": phone,
                    "status": "pending",
                    "plan": "all_models",
                    "expiry": ""
                })

                save_users(users)

            # BEST MODEL
            for model_name, result in data.items():

                try:
                    value = result["normal"]["summary"]["value"]

                    if value > best_model_value:
                        best_model_value = value
                        best_model_name = model_name

                except:
                    pass

            # MODEL RANKING
            ranking = sorted(
                data.items(),
                key=lambda x: x[1]["normal"]["summary"]["value"],
                reverse=True
            )

        return render_template(
            "index.html",
            data=data,
            goal_result=goal_result,
            is_premium=is_premium,
            best_model_name=best_model_name,
            best_model_value=best_model_value,
            ranking=ranking
        )

    except Exception as e:
        return f"APP ERROR: {str(e)}"
# =========================================================
# 🚀 ADMIN ROUTE (FIXED SAFE)
# =========================================================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    safe_users = [u for u in users if isinstance(u, dict)]

    monthly_users = len([u for u in safe_users if u.get("status") == "approved_monthly"])
    yearly_users = len([u for u in safe_users if u.get("status") == "approved_yearly"])

    monthly_revenue = monthly_users * PRICING["monthly"]
    yearly_revenue = yearly_users * PRICING["yearly"]

    total_revenue = monthly_revenue + yearly_revenue

    return render_template(
        "admin.html",
        users=safe_users,
        total_users=len(safe_users),
        pending_users=len([u for u in safe_users if u.get("status") == "pending"]),
        approved_monthly=monthly_users,
        approved_yearly=yearly_users,
        rejected_users=len([u for u in safe_users if u.get("status") == "rejected"]),
        monthly_revenue=monthly_revenue,
        yearly_revenue=yearly_revenue,
        total_revenue=total_revenue
    )
# =========================================================
# ✅ APPROVE USER
# =========================================================
@app.route("/approve/<code>/<plan>")
def approve(code, plan):

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    for u in users:

        if u.get("code") == code:

            if plan == "monthly":
                u["status"] = "approved_monthly"
                u["plan"] = "Monthly"

            elif plan == "yearly":
                u["status"] = "approved_yearly"
                u["plan"] = "Yearly"

            u["expiry"] = "ACTIVE"

    save_users(users)

    return redirect("/admin")


# =========================================================
# ❌ REJECT USER
# =========================================================
@app.route("/reject/<code>")
def reject(code):

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    for u in users:
        if u.get("code") == code:
            u["status"] = "rejected"

    save_users(users)

    return redirect("/admin")


# =========================================================
# 🔄 CANCEL SUBSCRIPTION
# =========================================================
@app.route("/cancel/<code>")
def cancel(code):

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    for u in users:

        if u.get("code") == code:
            u["status"] = "pending"
            u["plan"] = ""
            u["expiry"] = ""

    save_users(users)

    return redirect("/admin")
# =========================================================
# 🚀 RUN (RENDER SAFE)
# =========================================================
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
