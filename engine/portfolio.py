"""
=========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform

Portfolio Construction Engine

This module builds institutional investment portfolios
based on investment strategy.

Supported Models

• Dividend Blue Chip
• Aggressive Growth
• Banking Dominance
• Value Investing
• High Dividend Income

=========================================================
"""

import json


# ==========================================================
# LOAD COMPANY DATABASE
# ==========================================================

def load_companies():

    with open("data/companies.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================================================
# INVESTMENT MODELS
# ==========================================================

PORTFOLIO_MODELS = {

    "dividend": [
        "EQTY",
        "COOP",
        "KCB",
        "SCOM"
    ],

    "growth": [
        "SCOM",
        "EQTY",
        "NCBA",
        "EABL"
    ],

    "banking": [
        "EQTY",
        "KCB",
        "COOP",
        "NCBA"
    ],

    "value": [
        "EQTY",
        "COOP",
        "KEGN",
        "KCB"
    ],

    "income": [
        "COOP",
        "EQTY",
        "KCB",
        "KEGN"
    ]

}


# ==========================================================
# MODEL DESCRIPTION
# ==========================================================

MODEL_DESCRIPTION = {

    "dividend":
        "Focuses on stable dividend-paying companies.",

    "growth":
        "Focuses on long-term capital appreciation.",

    "banking":
        "Concentrated exposure to the banking sector.",

    "value":
        "Targets undervalued companies with strong fundamentals.",

    "income":
        "Designed for investors seeking regular passive income."

}


# ==========================================================
# BUILD PORTFOLIO
# ==========================================================

def build_portfolio(model="dividend"):

    companies = load_companies()

    codes = PORTFOLIO_MODELS.get(
        model,
        PORTFOLIO_MODELS["dividend"]
    )

    portfolio = []

    for company in companies:

        if company["code"] in codes:

            portfolio.append(company)

    return portfolio


# ==========================================================
# EQUAL WEIGHT ALLOCATION
# ==========================================================

def equal_weight(portfolio):

    weight = round(100 / len(portfolio), 2)

    allocation = []

    for company in portfolio:

        allocation.append({

            "code": company["code"],

            "name": company["name"],

            "weight": weight

        })

    return allocation


# ==========================================================
# CAPITAL ALLOCATION
# ==========================================================

def allocate_capital(monthly, allocation):

    plan = []

    for asset in allocation:

        plan.append({

            "code": asset["code"],

            "name": asset["name"],

            "weight": asset["weight"],

            "monthly_amount":
                round(monthly * asset["weight"] / 100, 2)

        })

    return plan


# ==========================================================
# PORTFOLIO SUMMARY
# ==========================================================

def portfolio_summary(portfolio):

    sectors = {}

    average_quality = 0
    average_health = 0
    average_dividend = 0

    for company in portfolio:

        sector = company["sector"]

        sectors[sector] = sectors.get(sector, 0) + 1

        average_quality += company["quality_score"]
        average_health += company["health_score"]
        average_dividend += company["dividend_yield"]

    n = len(portfolio)

    return {

        "companies": n,

        "sectors": sectors,

        "quality_score":
            round(average_quality / n, 1),

        "health_score":
            round(average_health / n, 1),

        "average_dividend":
            round(average_dividend / n, 2)

    }


# ==========================================================
# PORTFOLIO RATING
# ==========================================================

def portfolio_rating(score):

    if score >= 95:
        return "★★★★★ Elite"

    if score >= 90:
        return "★★★★☆ Excellent"

    if score >= 80:
        return "★★★★ Good"

    if score >= 70:
        return "★★★ Moderate"

    return "★★ High Risk"


# ==========================================================
# BUILD COMPLETE MODEL
# ==========================================================

def create_portfolio(model, monthly):

    portfolio = build_portfolio(model)

    allocation = equal_weight(portfolio)

    investment_plan = allocate_capital(
        monthly,
        allocation
    )

    summary = portfolio_summary(portfolio)

    summary["rating"] = portfolio_rating(
        summary["health_score"]
    )

    return {

        "portfolio": portfolio,

        "allocation": allocation,

        "plan": investment_plan,

        "summary": summary,

        "model": model,

        "description":
            MODEL_DESCRIPTION.get(model, "")

    }
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
    # -----------------------------------------------------

    # PORTFOLIO WEIGHTS

    # -----------------------------------------------------

    weights = institutional_allocator(R, mode)

    weights = apply_model_bias(weights, model)



    if len(weights) > len(assets):

        weights = weights[:len(assets)]

        weights = weights / np.sum(weights)
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
