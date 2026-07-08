# =========================================================
# JOBURA WEALTH®
# PORTFOLIO ENGINE
# Institutional Portfolio Construction
# =========================================================

import numpy as np

from engine.research import (
    DIVIDEND_DATABASE,
    estimate_dividend_yields
)
# =========================================================
# PORTFOLIO CONSTRAINTS
# =========================================================

MIN_WEIGHT = 0.03
MAX_WEIGHT = 0.40

REBALANCE_PERIOD = 12
# =========================================================
# COMPANY ANALYTICS
# =========================================================

def company_analytics(code, capital):

    profile = DIVIDEND_DATABASE.get(code, {})

    dividend_yield = profile.get("base_yield", 0.0)
    growth = profile.get("growth", 0.0)
    quality = profile.get("quality", 0.0)
    payout = profile.get("payout", 0.0)
    stability = profile.get("stability", 0.0)
    beta = profile.get("beta", 1.0)

    income = capital * dividend_yield

    health = (
        quality * 40
        + stability * 30
        + (1 - beta) * 20
        + (1 - payout) * 10
    )

    health = np.clip(health, 0, 100)

    return {

        "yield": round(dividend_yield * 100, 2),

        "growth": round(growth * 100, 2),

        "quality": round(quality * 100, 1),

        "stability": round(stability * 100, 1),

        "health": round(float(health), 1),

        "income": round(float(income), 2),

        "beta": beta,

        "policy": profile.get("policy"),

        "sector": profile.get("sector"),

        "roe": round(profile.get("roe", 0) * 100, 1),

        "pe": profile.get("pe"),

        "pb": profile.get("pb"),

        "credit": profile.get("credit"),

        "esg": profile.get("esg")

    }
    # =========================================================
# PORTFOLIO CONSTRUCTION ENGINE
# =========================================================

def build_portfolio(
    assets,
    weights,
    capital,
    dividends,
    invested,
    annual_return
):
    """
    Builds the institutional portfolio breakdown.
    """

    breakdown = []

    asset_values = capital + dividends

    for i, asset in enumerate(assets):

        code = asset[1]

        analytics = company_analytics(
            code,
            capital[i]
        )

        invested_asset = invested * weights[i]

        breakdown.append({

            # -----------------------------------
            # Identity
            # -----------------------------------
            "asset": asset[0],
            "code": code,

            # -----------------------------------
            # Allocation
            # -----------------------------------
            "allocation_pct": round(weights[i] * 100, 2),

            # -----------------------------------
            # Investment
            # -----------------------------------
            "capital": round(float(invested_asset), 2),

            "current_value": round(float(capital[i]), 2),

            "capital_gain": round(
                float(capital[i] - invested_asset),
                2
            ),

            # -----------------------------------
            # Income
            # -----------------------------------
            "dividends": round(
                float(dividends[i]),
                2
            ),

            "total_return": round(
                float(asset_values[i]),
                2
            ),

            # -----------------------------------
            # Institutional Analytics
            # -----------------------------------
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

            "esg": analytics["esg"],

            "annual_return": round(
                annual_return * 100,
                2
            )

        })

    return breakdown
    # =========================================================
# PORTFOLIO BREAKDOWN TABLE
# =========================================================

def build_portfolio_breakdown(
    assets,
    weights,
    capital,
    dividends,
    invested,
    company_analytics
):
    """
    Builds the institutional asset table shown
    in the dashboard.

    Returns
    -------
    list
        List of dictionaries.
    """

    breakdown = []

    asset_values = capital + dividends

    for i, asset in enumerate(assets):

        invested_asset = invested * weights[i]

        code = asset[1]

        analytics = company_analytics(
            code,
            capital[i]
        )

        breakdown.append({

            # -----------------------------------
            # Identity
            # -----------------------------------
            "asset": asset[0],
            "code": code,

            # -----------------------------------
            # Allocation
            # -----------------------------------
            "allocation_pct": round(
                weights[i] * 100,
                2
            ),

            # -----------------------------------
            # Capital
            # -----------------------------------
            "capital": round(
                float(invested_asset),
                2
            ),

            "current_value": round(
                float(capital[i]),
                2
            ),

            "capital_gain": round(
                float(capital[i] - invested_asset),
                2
            ),

            # -----------------------------------
            # Income
            # -----------------------------------
            "dividends": round(
                float(dividends[i]),
                2
            ),

            "total_return": round(
                float(asset_values[i]),
                2
            ),

            # -----------------------------------
            # Institutional Analytics
            # -----------------------------------
            "dividend_yield":
                analytics["yield"],

            "dividend_growth":
                analytics["growth"],

            "dividend_health":
                analytics["health"],

            "quality_score":
                analytics["quality"],

            "stability_score":
                analytics["stability"],

            "estimated_income":
                analytics["income"],

            "beta":
                analytics["beta"],

            "policy":
                analytics["policy"],

            "sector":
                analytics["sector"],

            "roe":
                analytics["roe"],

            "pe":
                analytics["pe"],

            "pb":
                analytics["pb"],

            "credit":
                analytics["credit"],

            "esg":
                analytics["esg"]

        })

    return breakdown
    # =========================================================
# MONTHLY INVESTMENT PLAN
# =========================================================

def build_monthly_plan(
    assets,
    weights,
    monthly
):
    """
    Monthly allocation plan.
    """

    monthly_alloc = monthly * weights

    plan = []

    for i, asset in enumerate(assets):

        plan.append({

            "name": asset[0],

            "percent": round(
                weights[i] * 100,
                2
            ),

            "kes": round(
                monthly_alloc[i],
                2
            )

        })

    return plan
    # =========================================================
# RETURNS TABLE
# =========================================================

def build_returns_table(
    assets,
    weights,
    capital,
    dividends,
    invested,
    annual_return
):
    """
    Asset performance table.
    """

    table = []

    for i, asset in enumerate(assets):

        invested_asset = invested * weights[i]

        table.append({

            "asset": asset[0],

            "capital": round(
                invested_asset,
                2
            ),

            "value": round(
                float(capital[i]),
                2
            ),

            "gain": round(
                float(capital[i] - invested_asset),
                2
            ),

            "dividends": round(
                float(dividends[i]),
                2
            ),

            "total": round(
                float(capital[i] + dividends[i]),
                2
            ),

            "annual_return": round(
                annual_return * 100,
                2
            )

        })

    return table
    # ==========================================================
# PART 7 — PORTFOLIO SUMMARY ENGINE
# ==========================================================

def build_summary(
    invested,
    portfolio_value,
    dividends,
    annual_return,
    cagr,
    volatility,
    sharpe,
    max_drawdown,
    years,
    inflation=0.05
):
    """
    Builds the institutional summary statistics.
    """

    invested = float(invested)
    portfolio_value = float(portfolio_value)

    real_value = portfolio_value / ((1 + inflation) ** years)

    summary = {

        "invested":
            round(invested, 2),

        "value":
            round(portfolio_value, 2),

        "real_value":
            round(real_value, 2),

        "dividends":
            round(float(dividends), 2),

        "annual_return":
            round(float(annual_return) * 100, 2),

        "cagr":
            round(float(cagr) * 100, 2),

        "volatility":
            round(float(volatility) * 100, 2),

        "sharpe":
            round(float(sharpe), 2),

        "max_drawdown":
            round(float(max_drawdown) * 100, 2)
    }

    return summary
    # ==========================================================
# PORTFOLIO HEALTH ENGINE
# ==========================================================

def portfolio_health(
    weights,
    assets,
    capital,
    dividends
):
    """
    Computes the institutional health score
    of the portfolio.
    """

    total_value = float(np.sum(capital + dividends))

    if total_value <= 0:

        return {

            "score": 0,

            "quality": 0,

            "income": 0,

            "diversification": 0,

            "risk": 0

        }

    # ------------------------------------------------------
    # QUALITY
    # ------------------------------------------------------
    quality = 0

    for i, asset in enumerate(assets):

        profile = DIVIDEND_DATABASE.get(asset[1], {})

        quality += (

            profile.get("quality", 0.50)

            * weights[i]

        )

    quality *= 100

    # ------------------------------------------------------
    # INCOME
    # ------------------------------------------------------
    income = 0

    for i, asset in enumerate(assets):

        profile = DIVIDEND_DATABASE.get(asset[1], {})

        income += (

            profile.get("base_yield", 0.04)

            * weights[i]

        )

    income = min(income * 1000, 100)

    # ------------------------------------------------------
    # DIVERSIFICATION
    # ------------------------------------------------------
    hhi = np.sum(np.square(weights))

    diversification = (1 - hhi)

    diversification *= 125

    diversification = np.clip(
        diversification,
        0,
        100
    )

    # ------------------------------------------------------
    # RISK
    # ------------------------------------------------------
    beta = 0

    for i, asset in enumerate(assets):

        profile = DIVIDEND_DATABASE.get(asset[1], {})

        beta += (

            profile.get("beta", 1.0)

            * weights[i]

        )

    risk = max(

        0,

        100 - abs(beta - 1) * 100

    )

    # ------------------------------------------------------
    # FINAL SCORE
    # ------------------------------------------------------
    score = (

        quality * 0.35 +

        income * 0.20 +

        diversification * 0.25 +

        risk * 0.20

    )

    return {

        "score": round(score, 1),

        "quality": round(quality, 1),

        "income": round(income, 1),

        "diversification": round(diversification, 1),

        "risk": round(risk, 1)

    }
    # ==========================================================
# INSTITUTIONAL RECOMMENDATION ENGINE
# ==========================================================

def recommend_asset(code):
    """
    Generates an institutional recommendation
    for a single company.
    """

    profile = DIVIDEND_DATABASE.get(code, {})

    quality = profile.get("quality", 0.50)

    stability = profile.get("stability", 0.50)

    growth = profile.get("growth", 0.00)

    dividend = profile.get("base_yield", 0.00)

    beta = profile.get("beta", 1.00)

    score = (

        quality * 35 +

        stability * 25 +

        growth * 20 +

        dividend * 300 +

        (1.20 - beta) * 20

    )

    score = np.clip(score, 0, 100)

    # -----------------------------------------------------
    # Recommendation
    # -----------------------------------------------------
    if score >= 85:

        action = "Strong Buy"

    elif score >= 75:

        action = "Buy"

    elif score >= 60:

        action = "Hold"

    elif score >= 45:

        action = "Reduce"

    else:

        action = "Sell"

    return {

        "score": round(float(score), 1),

        "action": action

    }
   # ==========================================================
# BUILD PORTFOLIO RECOMMENDATIONS
# ==========================================================

def portfolio_recommendations(assets):
    """
    Generates recommendations
    for every asset.
    """

    recommendations = []

    for asset in assets:

        rec = recommend_asset(asset[1])

        recommendations.append({

            "asset": asset[0],

            "code": asset[1],

            "score": rec["score"],

            "recommendation": rec["action"]

        })

    return recommendations 
# ==========================================================
# MASTER PORTFOLIO ENGINE
# ==========================================================

def build_portfolio(
    assets,
    weights,
    capital,
    dividends,
    invested,
    annual_return,
    cagr,
    volatility,
    sharpe,
    max_drawdown,
    years
):
    """
    Builds the complete institutional portfolio.

    Returns everything required by the dashboard.
    """

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------
    summary = build_summary(
        invested=invested,
        portfolio_value=float(np.sum(capital + dividends)),
        dividends=float(np.sum(dividends)),
        annual_return=annual_return,
        cagr=cagr,
        volatility=volatility,
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        years=years
    )

    # ------------------------------------------------------
    # Asset Breakdown
    # ------------------------------------------------------
    breakdown = build_portfolio_breakdown(
        assets=assets,
        weights=weights,
        capital=capital,
        dividends=dividends,
        invested=invested,
        company_analytics=company_analytics
    )

    # ------------------------------------------------------
    # Monthly Investment Plan
    # ------------------------------------------------------
    monthly_amount = invested / (years * 12)

    plan = build_monthly_plan(
        assets,
        weights,
        monthly_amount
    )

    # ------------------------------------------------------
    # Returns Table
    # ------------------------------------------------------
    returns = build_returns_table(
        assets,
        weights,
        capital,
        dividends,
        invested,
        annual_return
    )

    # ------------------------------------------------------
    # Portfolio Health
    # ------------------------------------------------------
    health = portfolio_health(
        weights,
        assets,
        capital,
        dividends
    )

    # ------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------
    recommendations = portfolio_recommendations(
        assets
    )

    # ------------------------------------------------------
    # Final Package
    # ------------------------------------------------------
    return {

        "summary": summary,

        "assets": breakdown,

        "plan": plan,

        "returns": returns,

        "health": health,

        "recommendations": recommendations

    }
