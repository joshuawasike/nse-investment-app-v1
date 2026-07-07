# ==========================================================
# JOBURA WEALTH®
# NSE Institutional Wealth Management Platform
# Professional Analytics Suite
# Version 2026
# ==========================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

import os
import json
import random
import base64
import io

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datetime import datetime

# ==========================================================
# ENGINE MODULES
# ==========================================================

from engine.simulation import simulate_market
from engine.portfolio import build_portfolio
from engine.analytics import portfolio_summary
from engine.ai import investment_advisor
from engine.research import (
    company_database,
    ASSETS,
    DIVIDEND_DATABASE,
    DIVIDEND_BASE,
    estimate_dividend_yields
)
from engine.risk import portfolio_risk
from engine.retirement import retirement_projection
from engine.reports import create_report

from engine.utils import (
    load_json,
    save_json,
    today,
    money,
    percent,
    platform
)
from engine.corporate_actions import (
    CORPORATE_ACTIONS,
    apply_corporate_actions
)
# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

app.secret_key = "JOBURA_WEALTH_2026"

# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

STATIC_DIR = os.path.join(BASE_DIR, "static")

# ==========================================================
# JSON DATABASE FILES
# ==========================================================

USERS_FILE = "users.json"

COMPANIES_FILE = "companies.json"

DIVIDENDS_FILE = "dividends.json"

MARKET_FILE = "market_data.json"

MODELS_FILE = "portfolio_models.json"

SECTORS_FILE = "sectors.json"

AI_RULES_FILE = "ai_rules.json"

RISK_FILE = "risk_profiles.json"

ECONOMY_FILE = "economic_indicators.json"

SUBSCRIPTIONS_FILE = "subscriptions.json"

TRANSACTIONS_FILE = "transactions.json"

# ==========================================================
# LOAD DATABASES
# ==========================================================

companies = load_json(
    os.path.join(DATA_DIR, COMPANIES_FILE)
)

users = load_json(
    os.path.join(DATA_DIR, USERS_FILE)
)

dividends = load_json(
    os.path.join(DATA_DIR, DIVIDENDS_FILE)
)

market = load_json(
    os.path.join(DATA_DIR, MARKET_FILE)
)

portfolio_models = load_json(
    os.path.join(DATA_DIR, MODELS_FILE)
)

sectors = load_json(
    os.path.join(DATA_DIR, SECTORS_FILE)
)

ai_rules = load_json(
    os.path.join(DATA_DIR, AI_RULES_FILE)
)

risk_profiles = load_json(
    os.path.join(DATA_DIR, RISK_FILE)
)

economic = load_json(
    os.path.join(DATA_DIR, ECONOMY_FILE)
)

subscriptions = load_json(
    os.path.join(DATA_DIR, SUBSCRIPTIONS_FILE)
)

transactions = load_json(
    os.path.join(DATA_DIR, TRANSACTIONS_FILE)
)

# ==========================================================
# PLATFORM INFORMATION
# ==========================================================

APP = platform()

# ==========================================================
# GLOBAL SETTINGS
# ==========================================================

COMMUNITY_PLAN = "Community Edition"

PROFESSIONAL_PLAN = "Professional Edition"

INSTITUTIONAL_PLAN = "Institutional Edition"

DEFAULT_MARKET = "Normal"

DEFAULT_MODEL = "Dividend"

CURRENCY = "KES"

# ==========================================================
# APPLICATION HOME
# ==========================================================

@app.route("/")
def home():

    return render_template(

        "dashboard.html",

        app=APP,

        companies=companies,

        market=market,

        user=session.get("user"),

        premium=session.get("premium", False)

    )

@app.route("/companies")
def company_list():

    files = glob.glob("NSE_data_all_stock_*.csv")

    if not files:
        return "No CSV files found"

    names = []

    for f in files:
        try:
            temp = pd.read_csv(f)

            temp.columns = temp.columns.astype(str).str.strip().str.upper()

            possible_cols = [
                "NAME",
                "COMPANY",
                "SECURITY",
                "SYMBOL",
                "STOCK",
                "ISSUER"
            ]

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
# ==========================================================
# SECURITY CONFIGURATION
# ==========================================================

ADMIN_PASSWORD = "Jobura@542542"

USERS_PATH = os.path.join(DATA_DIR, USERS_FILE)

# ==========================================================
# USER MANAGEMENT
# ==========================================================

def load_users():
    return load_json(USERS_PATH)


def save_users(users):
    save_json(USERS_PATH, users)


def is_active(user):

    if not isinstance(user, dict):
        return False

    status = user.get("status", "").lower()

    return (
        "monthly" in status
        or
        "yearly" in status
        or
        "professional" in status
        or
        "institutional" in status
    )

# ==========================================================
# PAYMENT CONFIGURATION
# ==========================================================

PAYMENT_INFO = {

    "paybill": "542542",

    "account": "31909",

    "business_name": "Jobura Solutions",

    "currency": "KES"

}

# ==========================================================
# SUBSCRIPTION PRICING
# ==========================================================

PRICING = {

    "Community": {
        "monthly": 0,
        "yearly": 0
    },

    "Professional": {
        "monthly": 400,
        "yearly": 4000
    },

    "Institutional": {
        "monthly": 2000,
        "yearly": 18000
    }

}
from engine.research import (
    load_data,
    get_df,
    estimate_market_statistics,
    get_market_stats,
    get_model_assets,
    estimate_dividend_yields
)

# =========================================================
# 🏦 CORPORATE ACTION DATABASE
# =========================================================

CORPORATE_ACTIONS = {

    "EQTY":{

        "split":0.01,
        "bonus":0.03,
        "rights":0.04,
        "buyback":0.01,
        "special_dividend":0.02

    },

    "KCB":{

        "split":0.01,
        "bonus":0.02,
        "rights":0.03,
        "buyback":0.02,
        "special_dividend":0.01

    },

    "COOP":{

        "split":0.00,
        "bonus":0.04,
        "rights":0.02,
        "buyback":0.01,
        "special_dividend":0.02

    },

    "SCOM":{

        "split":0.00,
        "bonus":0.01,
        "rights":0.01,
        "buyback":0.04,
        "special_dividend":0.05

    },

    "EABL":{

        "split":0.00,
        "bonus":0.02,
        "rights":0.01,
        "buyback":0.02,
        "special_dividend":0.04

    },

    "KEGN":{

        "split":0.00,
        "bonus":0.01,
        "rights":0.02,
        "buyback":0.01,
        "special_dividend":0.01

    },

    "NCBA":{

        "split":0.01,
        "bonus":0.02,
        "rights":0.03,
        "buyback":0.02,
        "special_dividend":0.02

    },

    "KQ":{

        "split":0.00,
        "bonus":0.00,
        "rights":0.08,
        "buyback":0.00,
        "special_dividend":0.00

    }

}
# =========================================================
# 🏦 CORPORATE ACTION ENGINE
# =========================================================

def apply_corporate_actions(capital, code):

    profile = CORPORATE_ACTIONS.get(code)

    if profile is None:
        return capital, 0.0

    bonus = 0.0

    # Bonus shares
    if np.random.rand() < profile["bonus"]:

        capital *= 1.10

    # Rights issue
    if np.random.rand() < profile["rights"]:

        capital *= 1.05

    # Share buyback
    if np.random.rand() < profile["buyback"]:

        capital *= 1.03

    # Stock split
    if np.random.rand() < profile["split"]:

        capital *= 1.00

    # Special dividend
    if np.random.rand() < profile["special_dividend"]:

        bonus = capital * 0.03

    return capital, bonus

# =========================================================
# INSTITUTIONAL COMPANY ANALYTICS
# =========================================================
def company_analytics(code, capital):

    profile = DIVIDEND_DATABASE.get(code, {})

    dividend_yield = profile.get("base_yield",0)

    growth = profile.get("growth",0)

    quality = profile.get("quality",0)

    payout = profile.get("payout",0)

    stability = profile.get("stability",0)

    beta = profile.get("beta",1)

    income = capital * dividend_yield

    health = (

        quality*40 +

        stability*30 +

        (1-beta)*20 +

        (1-payout)*10

    )

    health = max(0,min(100,health))

    return{

        "yield":round(dividend_yield*100,2),

        "growth":round(growth*100,2),

        "quality":round(quality*100,1),

        "stability":round(stability*100,1),

        "health":round(health,1),

        "income":round(income,2),

        "beta":beta,

        "policy":profile.get("policy"),

        "sector":profile.get("sector"),

        "roe":round(profile.get("roe",0)*100,1),

        "pe":profile.get("pe"),

        "pb":profile.get("pb"),

        "credit":profile.get("credit"),

        "esg":profile.get("esg")

    }
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
# 🌍 INSTITUTIONAL ECONOMIC REGIME ENGINE V2
# =========================================================

ECONOMIC_REGIMES = {

    # -----------------------------------------------------
    # NORMAL ECONOMY
    # -----------------------------------------------------
    "normal": {

        # Multiplier applied to historical expected returns
        "drift": 1.00,

        # Absolute monthly return adjustment
        "alpha": 0.0000,

        # Volatility multiplier
        "vol": 1.00,

        # Dividend adjustment
        "dividend": 1.00,

        # Corporate earnings adjustment
        "earnings": 1.00,

        # Sector performance
        "sector": {

            "Banking":   1.00,
            "Telecom":   1.00,
            "Consumer":  1.00,
            "Utilities": 1.00,
            "Airline":   1.00

        }

    },

    # -----------------------------------------------------
    # BULL MARKET
    # -----------------------------------------------------
    "bull": {

        # Historical returns increase slightly
        "drift": 1.10,

        # Extra monthly return boost
        "alpha": 0.0020,

        # Lower volatility
        "vol": 0.80,

        # Higher dividend growth
        "dividend": 1.12,

        # Higher earnings
        "earnings": 1.15,

        "sector": {

            "Banking":   1.20,
            "Telecom":   1.12,
            "Consumer":  1.15,
            "Utilities": 1.00,
            "Airline":   1.50

        }

    },

    # -----------------------------------------------------
    # BEAR MARKET
    # -----------------------------------------------------
    "bear": {

        # Slight reduction in historical returns
        "drift": 0.90,

        # Negative monthly return adjustment
        "alpha": -0.0020,

        # Higher volatility
        "vol": 1.55,

        # Dividend cuts
        "dividend": 0.82,

        # Earnings contraction
        "earnings": 0.85,

        "sector": {

            "Banking":   0.75,
            "Telecom":   0.95,
            "Consumer":  0.82,
            "Utilities": 1.05,
            "Airline":   0.30

        }

    }

}
# =========================================================
# 🌍 INSTITUTIONAL MARKET GENERATOR V13
# Historical NSE Monte Carlo Engine
# =========================================================
def generate_market(mode, N, drift, vol, momentum):

    stats = get_market_stats()

    periods = 300

    # -----------------------------------------------------
    # FALLBACK
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
    # MATCH NSE UNIVERSE
    # -----------------------------------------------------
    codes = [asset[1] for asset in ASSETS]

    available = [
        c for c in codes
        if (
            c in mu.index and
            c in sigma.index and
            c in cov.index
        )
    ]

    if len(available) < 2:

        return np.random.normal(
            drift,
            vol,
            (N, periods)
        )

    mu = mu.loc[available]
    sigma = sigma.loc[available]
    cov = cov.loc[available, available]

    # -----------------------------------------------------
    # ECONOMIC REGIME
    # -----------------------------------------------------
    regime = ECONOMIC_REGIMES.get(
        mode,
        ECONOMIC_REGIMES["normal"]
    )

    # -----------------------------------------------------
    # SECTOR ADJUSTMENTS
    # -----------------------------------------------------
    sector_multiplier = []

    for code in available:

        profile = DIVIDEND_DATABASE.get(code, {})

        sector = profile.get(
            "sector",
            "Banking"
        )

        sector_multiplier.append(

            regime["sector"].get(
                sector,
                1.0
            )

        )

    sector_multiplier = np.array(sector_multiplier)

    # -----------------------------------------------------
    # EXPECTED RETURNS
    # -----------------------------------------------------
    mu = (
        mu
        * sector_multiplier
        * regime["drift"]
    ) + regime["alpha"]

    mu = np.clip(
        mu,
        -0.015,
        0.015
    )

    # -----------------------------------------------------
    # VOLATILITY
    # -----------------------------------------------------
    sigma *= np.sqrt(regime["vol"])

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
    # FAT-TAIL MONTE CARLO
    # -----------------------------------------------------
    shocks = np.random.standard_t(
        df=6,
        size=(len(mu), periods)
    )

    correlated = L @ shocks

    # -----------------------------------------------------
    # MOMENTUM PROCESS
    # -----------------------------------------------------
    phi = np.clip(momentum, 0.15, 0.95)

    trend = np.zeros_like(correlated)

    for t in range(1, periods):

        trend[:, t] = (

            phi * trend[:, t-1]

            + correlated[:, t]

        )

    # -----------------------------------------------------
    # FINAL RETURNS
    # -----------------------------------------------------
    R = mu.values[:, None] + trend

    # -----------------------------------------------------
    # MATCH HISTORICAL VOLATILITY
    # -----------------------------------------------------
    current_std = np.std(
        R,
        axis=1,
        keepdims=True
    )

    current_std[current_std == 0] = 1e-8

    target_std = sigma.values[:, None]

    R *= target_std / current_std

    # -----------------------------------------------------
    # EXTREME EVENT SIMULATION
    # -----------------------------------------------------
    shock_probability = 0.015

    disaster = np.random.rand(
        len(mu),
        periods
    ) < shock_probability

    if mode == "bull":

        disaster_returns = np.random.uniform(
            -0.04,
            -0.02,
            disaster.shape
        )

    elif mode == "bear":

        disaster_returns = np.random.uniform(
            -0.12,
            -0.05,
            disaster.shape
        )

    else:

        disaster_returns = np.random.uniform(
            -0.08,
            -0.03,
            disaster.shape
        )

    R[disaster] += disaster_returns[disaster]

    # -----------------------------------------------------
    # SAFETY LIMITS
    # -----------------------------------------------------
    R = np.clip(
        R,
        -0.15,
        0.18
    )

    # -----------------------------------------------------
    # PAD IF NECESSARY
    # -----------------------------------------------------
    if len(mu) < N:

        extra = np.random.normal(

            drift,

            vol,

            (N-len(mu), periods)

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

            stability = profile.get("stability", 0.90)

            payout = profile.get("payout", 0.40)

            years_elapsed = m / 12

            dividend_yield = forecast_dividend_yield(
                code,
                years_elapsed,
                mode
            )

            current_month = (m % 12) + 1

            if current_month in payment_months:

                payments = len(payment_months)

                dividend = (
                    capital[i]
                    * dividend_yield
                    * payout
                    * regime_multiplier
                    / payments
                )

                capital[i], bonus = apply_corporate_actions(
                    capital[i],
                    code
                )
    
                dividends[i] += dividend + bonus
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

        code = assets[i][1]

        analytics = company_analytics(
            code,
            capital[i]
        )

        breakdown.append({

        # -------------------------------
        # Basic Portfolio Information
        # -------------------------------
        "asset": assets[i][0],

        "code": code,

        "allocation_pct": round(weights[i] * 100, 2),

        "capital": round(float(invested_asset), 2),

        "current_value": round(float(capital[i]), 2),

        "capital_gain": round(
            float(capital[i] - invested_asset),
            2
        ),

        "dividends": round(
            float(dividends[i]),
            2
        ),

        "total_return": round(
            float(asset_values[i]),
            2
        ),

        # -------------------------------
        # Institutional Analytics
        # -------------------------------
        "dividend_yield": analytics["yield"],

        "dividend_growth": analytics["growth"],

        "dividend_health": analytics["health"],

        "quality_score": analytics["quality"],

        "stability_score": analytics["stability"],

        "estimated_income": analytics["income"],

        "beta": analytics["beta"],

        "policy": analytics["policy"],

        "sector": analytics["sector"],

        "roe": analytics["roe"],

        "pe": analytics["pe"],

        "pb": analytics["pb"],

        "credit": analytics["credit"],

        "esg": analytics["esg"]

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
