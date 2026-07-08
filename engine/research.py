# ==========================================================
# JOBURA WEALTH®
# RESEARCH ENGINE
# Institutional Market Research Module
# Version 2026
# ==========================================================

import os
import glob

import numpy as np
import pandas as pd

# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_DIR = os.path.join(DATA_DIR, "nse_csv")

# ==========================================================
# MARKET DATA CACHE
# ==========================================================

_market_cache = None
_market_statistics = None

# ==========================================================
# NSE COMPANY MASTER LIST
# (Company Name, Stock Code)
# ==========================================================

ASSETS = [

    ("Equity Bank", "EQTY"),

    ("KCB Group", "KCB"),

    ("Co-operative Bank", "COOP"),

    ("Safaricom", "SCOM"),

    ("East African Breweries", "EABL"),

    ("KenGen", "KEGN"),

    ("NCBA Group", "NCBA"),

    ("Kenya Airways", "KQ")

]

# ==========================================================
# COMPANY NAME LOOKUP
# ==========================================================

COMPANY_NAMES = {

    code: name

    for name, code in ASSETS

}

# ==========================================================
# MODEL UNIVERSES
# ==========================================================

MODEL_UNIVERSES = {

    "dividend": [

        "EQTY",
        "KCB",
        "COOP",
        "SCOM",
        "EABL",
        "KEGN",
        "NCBA"

    ],

    "growth": [

        "SCOM",
        "KQ",
        "NCBA",
        "EQTY",
        "KCB"

    ],

    "banking": [

        "EQTY",
        "KCB",
        "COOP",
        "NCBA"

    ],

    "value": [

        "KEGN",
        "EABL",
        "KQ",
        "NCBA"

    ],

    "income": [

        "SCOM",
        "EABL",
        "KCB",
        "EQTY",
        "COOP"

    ]

}

# ==========================================================
# DIVIDEND BASELINE YIELDS
# ==========================================================

DIVIDEND_BASE = {

    "EQTY": 0.075,

    "KCB": 0.068,

    "COOP": 0.082,

    "SCOM": 0.064,

    "EABL": 0.052,

    "KEGN": 0.055,

    "NCBA": 0.060,

    "KQ": 0.000

}

# ==========================================================
# INSTITUTIONAL COMPANY DATABASE
# ==========================================================

DIVIDEND_DATABASE = {

    "EQTY": {

        "sector": "Banking",

        "growth": 0.09,

        "base_yield": 0.075,

        "stability": 0.95,

        "quality": 0.95,

        "payout": 0.45,

        "months": [4, 9],

        "policy": "Semi-Annual",

        "roe": 0.24,

        "pe": 6.9,

        "pb": 1.5,

        "beta": 1.05,

        "credit": "A",

        "esg": 82

    },

    "KCB": {

        "sector": "Banking",

        "growth": 0.08,

        "base_yield": 0.068,

        "stability": 0.93,

        "quality": 0.93,

        "payout": 0.42,

        "months": [5],

        "policy": "Annual",

        "roe": 0.21,

        "pe": 5.8,

        "pb": 1.2,

        "beta": 1.08,

        "credit": "A",

        "esg": 79

    },

    "COOP": {

        "sector": "Banking",

        "growth": 0.075,

        "base_yield": 0.082,

        "stability": 0.97,

        "quality": 0.91,

        "payout": 0.55,

        "months": [5],

        "policy": "Annual",

        "roe": 0.18,

        "pe": 5.2,

        "pb": 1.1,

        "beta": 0.95,

        "credit": "A",

        "esg": 81

    },

    "SCOM": {

        "sector": "Telecom",

        "growth": 0.07,

        "base_yield": 0.064,

        "stability": 0.98,

        "quality": 0.96,

        "payout": 0.85,

        "months": [3,8],

        "policy": "Semi-Annual",

        "roe": 0.62,

        "pe": 12.5,

        "pb": 5.6,

        "beta": 0.82,

        "credit": "AAA",

        "esg": 90

    },

    "EABL": {

        "sector": "Consumer",

        "growth": 0.065,

        "base_yield": 0.052,

        "stability": 0.90,

        "quality": 0.93,

        "payout": 0.70,

        "months": [10],

        "policy": "Annual",

        "roe": 0.32,

        "pe": 13.8,

        "pb": 5.2,

        "beta": 0.95,

        "credit": "AA",

        "esg": 86

    },

    "KEGN": {

        "sector": "Utilities",

        "growth": 0.04,

        "base_yield": 0.055,

        "stability": 0.96,

        "quality": 0.90,

        "payout": 0.55,

        "months": [11],

        "policy": "Annual",

        "roe": 0.15,

        "pe": 7.4,

        "pb": 0.9,

        "beta": 0.60,

        "credit": "AA",

        "esg": 88

    },

    "NCBA": {

        "sector": "Banking",

        "growth": 0.08,

        "base_yield": 0.060,

        "stability": 0.91,

        "quality": 0.90,

        "payout": 0.42,

        "months": [5],

        "policy": "Annual",

        "roe": 0.19,

        "pe": 5.5,

        "pb": 1.1,

        "beta": 1.00,

        "credit": "A",

        "esg": 80

    },

    "KQ": {

        "sector": "Airline",

        "growth": 0.18,

        "base_yield": 0.00,

        "stability": 0.40,

        "quality": 0.55,

        "payout": 0.00,

        "months": [],

        "policy": "None",

        "roe": -0.08,

        "pe": None,

        "pb": 0.60,

        "beta": 1.90,

        "credit": "B",

        "esg": 62

    }

}
# ==========================================================
# LOAD NSE CSV FILES
# ==========================================================

def load_data(force_reload=False):
    """
    Load all NSE historical CSV files into memory.
    """

    global _market_cache

    if _market_cache is not None and not force_reload:
        return _market_cache

    database = {}

    csv_files = glob.glob(
        os.path.join(CSV_DIR, "*.csv")
    )

    for file in csv_files:

        try:

            df = pd.read_csv(file)

            df.columns = (
                df.columns
                .astype(str)
                .str.strip()
                .str.upper()
            )

            code = os.path.basename(file)

            code = os.path.splitext(code)[0]

            database[code] = df

        except Exception:

            continue

    _market_cache = database

    return database


# ==========================================================
# GET SINGLE COMPANY DATAFRAME
# ==========================================================

def get_df(code):
    """
    Returns one company's historical dataframe.
    """

    database = load_data()

    return database.get(code)


# ==========================================================
# COMPANY DATABASE
# ==========================================================

def company_database():
    """
    Returns all available companies.
    """

    return ASSETS


# ==========================================================
# MODEL ASSET SELECTION
# ==========================================================

def get_model_assets(model="dividend"):
    """
    Returns assets belonging to one investment model.
    """

    model = str(model).lower()

    codes = MODEL_UNIVERSES.get(
        model,
        MODEL_UNIVERSES["dividend"]
    )

    selected = []

    for company in ASSETS:

        if company[1] in codes:

            selected.append(company)

    return selected


# ==========================================================
# ESTIMATE MARKET STATISTICS
# ==========================================================

def estimate_market_statistics(force_reload=False):
    """
    Calculates historical statistics for all NSE companies.
    """

    global _market_statistics

    if _market_statistics is not None and not force_reload:
        return _market_statistics

    database = load_data(force_reload)

    returns = {}

    for code, df in database.items():

        try:

            # -------------------------------
            # Locate closing price
            # -------------------------------
            close_col = None

            for col in [

                "CLOSE",

                "ADJ CLOSE",

                "CLOSING PRICE",

                "PRICE"

            ]:

                if col in df.columns:

                    close_col = col

                    break

            if close_col is None:

                continue

            prices = (

                pd.to_numeric(

                    df[close_col],

                    errors="coerce"

                )

                .dropna()

            )

            if len(prices) < 30:

                continue

            r = prices.pct_change().dropna()

            if len(r) > 10:

                returns[code] = r

        except Exception:

            continue

    if len(returns) < 2:

        _market_statistics = None

        return None

    returns_df = pd.DataFrame(returns)

    statistics = {

        "returns": returns_df,

        "mu": returns_df.mean(),

        "sigma": returns_df.std(),

        "cov": returns_df.cov(),

        "corr": returns_df.corr()

    }

    _market_statistics = statistics

    return statistics


# ==========================================================
# GET MARKET STATISTICS
# ==========================================================

def get_market_stats():
    """
    Cached market statistics.
    """

    if _market_statistics is None:

        return estimate_market_statistics()

    return _market_statistics
# ==========================================================
# DIVIDEND YIELD ESTIMATION
# ==========================================================

def estimate_dividend_yields(mode="normal", model="dividend"):
    """
    Estimates forward dividend yields after adjusting
    for market regime.
    """

    regime_factor = {
        "normal": 1.00,
        "bull": 1.12,
        "bear": 0.82
    }.get(str(mode).lower(), 1.00)

    yields = {}

    assets = get_model_assets(model)

    for _, code in assets:

        profile = DIVIDEND_DATABASE.get(code, {})

        base = profile.get(
            "base_yield",
            DIVIDEND_BASE.get(code, 0.05)
        )

        growth = profile.get("growth", 0.00)

        stability = profile.get("stability", 0.90)

        payout = profile.get("payout", 0.40)

        y = (
            base
            * regime_factor
            * (1 + growth)
            * stability
            * (0.60 + payout)
        )

        yields[code] = float(
            np.clip(y, 0.00, 0.18)
        )

    return yields


# ==========================================================
# DIVIDEND FORECAST ENGINE
# ==========================================================

def forecast_dividend_yield(
        code,
        years_elapsed,
        mode="normal"
):
    """
    Forecast future dividend yield.
    """

    profile = DIVIDEND_DATABASE.get(code, {})

    base = profile.get(
        "base_yield",
        DIVIDEND_BASE.get(code, 0.05)
    )

    growth = profile.get("growth", 0.00)

    stability = profile.get("stability", 0.90)

    payout = profile.get("payout", 0.40)

    forecast = base * ((1 + growth) ** years_elapsed)

    if mode == "bull":
        forecast *= 1.10

    elif mode == "bear":
        forecast *= 0.80

    forecast *= stability

    forecast *= (0.60 + payout)

    return float(
        np.clip(
            forecast,
            0.00,
            0.18
        )
    )


# ==========================================================
# COMPANY ANALYTICS
# ==========================================================

def company_analytics(
        code,
        capital=0.0
):
    """
    Institutional company analytics.
    """

    profile = DIVIDEND_DATABASE.get(code, {})

    dividend_yield = profile.get("base_yield", 0)

    growth = profile.get("growth", 0)

    quality = profile.get("quality", 0)

    payout = profile.get("payout", 0)

    stability = profile.get("stability", 0)

    beta = profile.get("beta", 1)

    income = capital * dividend_yield

    health = (

        quality * 40 +

        stability * 30 +

        (1 - beta) * 20 +

        (1 - payout) * 10

    )

    health = max(
        0,
        min(100, health)
    )

    return {

        "yield":
            round(dividend_yield * 100, 2),

        "growth":
            round(growth * 100, 2),

        "quality":
            round(quality * 100, 1),

        "stability":
            round(stability * 100, 1),

        "health":
            round(health, 1),

        "income":
            round(income, 2),

        "beta":
            beta,

        "policy":
            profile.get("policy"),

        "sector":
            profile.get("sector"),

        "roe":
            round(
                profile.get("roe", 0) * 100,
                1
            ),

        "pe":
            profile.get("pe"),

        "pb":
            profile.get("pb"),

        "credit":
            profile.get("credit"),

        "esg":
            profile.get("esg")

    }


# ==========================================================
# DIVIDEND HEALTH SCORE
# ==========================================================

def dividend_health_score(
        code,
        stats=None
):
    """
    Dividend sustainability score.
    """

    profile = DIVIDEND_DATABASE.get(code, {})

    stability = profile.get(
        "stability",
        0.90
    )

    quality = profile.get(
        "quality",
        0.90
    )

    if stats is None:

        return float(

            np.clip(

                0.60 * stability +

                0.40 * quality,

                0.20,

                0.99

            )

        )

    try:

        mu = float(stats["mu"][code])

        sigma = float(stats["sigma"][code])

        score = (

            0.35 * stability +

            0.35 * quality +

            0.20 * np.clip(
                mu * 30,
                0,
                1
            ) +

            0.10 * np.clip(
                1 - sigma * 20,
                0,
                1
            )

        )

        return float(

            np.clip(
                score,
                0.20,
                0.99
            )

        )

    except Exception:

        return float(

            np.clip(

                0.60 * stability +

                0.40 * quality,

                0.20,

                0.99

            )

        )
  # ==========================================================
# INSTITUTIONAL ECONOMIC REGIME ENGINE
# ==========================================================

ECONOMIC_REGIMES = {

    "normal": {

        "drift": 1.00,

        "alpha": 0.0000,

        "vol": 1.00,

        "dividend": 1.00,

        "earnings": 1.00,

        "sector": {

            "Banking": 1.00,

            "Telecom": 1.00,

            "Consumer": 1.00,

            "Utilities": 1.00,

            "Airline": 1.00

        }

    },

    "bull": {

        "drift": 1.10,

        "alpha": 0.0020,

        "vol": 0.80,

        "dividend": 1.12,

        "earnings": 1.15,

        "sector": {

            "Banking": 1.20,

            "Telecom": 1.12,

            "Consumer": 1.15,

            "Utilities": 1.00,

            "Airline": 1.50

        }

    },

    "bear": {

        "drift": 0.90,

        "alpha": -0.0020,

        "vol": 1.55,

        "dividend": 0.82,

        "earnings": 0.85,

        "sector": {

            "Banking": 0.75,

            "Telecom": 0.95,

            "Consumer": 0.82,

            "Utilities": 1.05,

            "Airline": 0.30

        }

    }

}


# ==========================================================
# GET ECONOMIC REGIME
# ==========================================================

def get_regime(mode="normal"):
    """
    Returns the requested economic regime.
    """

    return ECONOMIC_REGIMES.get(

        str(mode).lower(),

        ECONOMIC_REGIMES["normal"]

    )


# ==========================================================
# APPLY MARKET REGIME TO RETURNS
# ==========================================================

def apply_regime(mu, sigma, mode="normal"):
    """
    Applies macro-economic adjustments to expected
    returns and volatility.
    """

    regime = get_regime(mode)

    mu = (

        mu * regime["drift"]

    ) + regime["alpha"]

    sigma = sigma * np.sqrt(regime["vol"])

    return mu, sigma


# ==========================================================
# APPLY SECTOR MULTIPLIERS
# ==========================================================

def apply_sector_adjustment(
        codes,
        mu,
        mode="normal"
):
    """
    Applies sector-specific adjustments.
    """

    regime = get_regime(mode)

    adjusted = []

    for code, value in zip(codes, mu):

        profile = DIVIDEND_DATABASE.get(code, {})

        sector = profile.get(
            "sector",
            "Banking"
        )

        multiplier = regime["sector"].get(

            sector,

            1.0

        )

        adjusted.append(

            value * multiplier

        )

    return np.array(adjusted)


# ==========================================================
# BUILD EXPECTED RETURN VECTOR
# ==========================================================

def expected_returns(
        codes,
        mode="normal"
):
    """
    Returns regime-adjusted expected returns.
    """

    stats = get_market_stats()

    if stats is None:

        return None

    mu = stats["mu"].copy()

    available = [

        c for c in codes

        if c in mu.index

    ]

    if len(available) == 0:

        return None

    mu = mu.loc[available]

    mu = apply_sector_adjustment(

        available,

        mu.values,

        mode

    )

    regime = get_regime(mode)

    mu = (

        mu * regime["drift"]

    ) + regime["alpha"]

    mu = np.clip(

        mu,

        -0.015,

        0.015

    )

    return mu


# ==========================================================
# BUILD VOLATILITY VECTOR
# ==========================================================

def expected_volatility(
        codes,
        mode="normal"
):
    """
    Returns adjusted historical volatility.
    """

    stats = get_market_stats()

    if stats is None:

        return None

    sigma = stats["sigma"].copy()

    available = [

        c for c in codes

        if c in sigma.index

    ]

    sigma = sigma.loc[available]

    regime = get_regime(mode)

    sigma *= np.sqrt(

        regime["vol"]

    )

    return sigma.values


# ==========================================================
# BUILD COVARIANCE MATRIX
# ==========================================================

def expected_covariance(
        codes,
        mode="normal"
):
    """
    Returns regime-adjusted covariance matrix.
    """

    stats = get_market_stats()

    if stats is None:

        return None

    cov = stats["cov"].copy()

    available = [

        c for c in codes

        if c in cov.index

    ]

    cov = cov.loc[

        available,

        available

    ]

    regime = get_regime(mode)

    cov *= regime["vol"]

    cov += np.eye(len(cov)) * 1e-8

    return cov.values   
# ==========================================================
# INSTITUTIONAL MARKET GENERATOR V13
# Historical NSE Monte Carlo Engine
# ==========================================================

def generate_market(
        mode,
        assets,
        drift=0.004,
        vol=0.015,
        momentum=0.75
):
    """
    Generates a correlated Monte Carlo return matrix
    using historical NSE statistics.
    """

    periods = 300

    stats = get_market_stats()

    # ------------------------------------------------------
    # FALLBACK
    # ------------------------------------------------------

    if stats is None:

        return np.random.normal(

            drift,

            vol,

            (len(assets), periods)

        )

    # ------------------------------------------------------
    # HISTORICAL DATA
    # ------------------------------------------------------

    mu = stats["mu"].copy()

    sigma = stats["sigma"].copy()

    cov = stats["cov"].copy()

    codes = [

        asset[1]

        for asset in assets

    ]

    available = [

        c for c in codes

        if (

            c in mu.index and

            c in sigma.index and

            c in cov.index

        )

    ]

    # ------------------------------------------------------
    # SAFETY
    # ------------------------------------------------------

    if len(available) < 2:

        return np.random.normal(

            drift,

            vol,

            (len(assets), periods)

        )

    mu = mu.loc[available]

    sigma = sigma.loc[available]

    cov = cov.loc[

        available,

        available

    ]

    # ------------------------------------------------------
    # APPLY ECONOMIC REGIME
    # ------------------------------------------------------

    regime = get_regime(mode)

    sector_mu = apply_sector_adjustment(

        available,

        mu.values,

        mode

    )

    mu = (

        sector_mu *

        regime["drift"]

    ) + regime["alpha"]

    mu = np.clip(

        mu,

        -0.015,

        0.015

    )

    sigma = sigma.values * np.sqrt(

        regime["vol"]

    )

    cov = cov.values * regime["vol"]

    cov += np.eye(len(cov)) * 1e-8

    # ------------------------------------------------------
    # POSITIVE DEFINITE MATRIX
    # ------------------------------------------------------

    try:

        L = np.linalg.cholesky(cov)

    except np.linalg.LinAlgError:

        eigvals, eigvecs = np.linalg.eigh(cov)

        eigvals[eigvals < 1e-8] = 1e-8

        cov = (

            eigvecs @

            np.diag(eigvals) @

            eigvecs.T

        )

        L = np.linalg.cholesky(cov)

    # ------------------------------------------------------
    # FAT-TAIL SHOCKS
    # ------------------------------------------------------

    shocks = np.random.standard_t(

        df=6,

        size=(len(mu), periods)

    )

    correlated = L @ shocks

    # ------------------------------------------------------
    # MOMENTUM
    # ------------------------------------------------------

    phi = np.clip(

        momentum,

        0.15,

        0.95

    )

    trend = np.zeros_like(correlated)

    for t in range(1, periods):

        trend[:, t] = (

            phi * trend[:, t-1]

            +

            correlated[:, t]

        )

    # ------------------------------------------------------
    # FINAL RETURNS
    # ------------------------------------------------------

    R = mu[:, None] + trend

    current_std = np.std(

        R,

        axis=1,

        keepdims=True

    )

    current_std[current_std == 0] = 1e-8

    target_std = sigma[:, None]

    R *= target_std / current_std

    # ------------------------------------------------------
    # EXTREME EVENTS
    # ------------------------------------------------------

    probability = 0.015

    disaster = np.random.rand(

        len(mu),

        periods

    ) < probability

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

    # ------------------------------------------------------
    # SAFETY LIMITS
    # ------------------------------------------------------

    R = np.clip(

        R,

        -0.15,

        0.18

    )

    # ------------------------------------------------------
    # PAD IF NECESSARY
    # ------------------------------------------------------

    if len(available) < len(assets):

        extra = np.random.normal(

            drift,

            vol,

            (

                len(assets) - len(available),

                periods

            )

        )

        R = np.vstack([

            R,

            extra

        ])

    return R[:len(assets)]
