"""
=========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform

Portfolio Simulation Engine

This module performs:

• Portfolio simulations
• Bull / Bear / Normal market scenarios
• Dividend projections
• Capital growth forecasting
• Multi-year wealth projections

=========================================================
"""

import random
import math


# =========================================================
# MARKET REGIMES
# =========================================================

MARKET_REGIMES = {

    "normal": {
        "growth": 0.12,
        "volatility": 0.16
    },

    "bull": {
        "growth": 0.21,
        "volatility": 0.20
    },

    "bear": {
        "growth": -0.08,
        "volatility": 0.28
    }

}


# =========================================================
# DEFAULT DIVIDEND YIELDS
# =========================================================

DIVIDENDS = {

    "EQTY":0.091,
    "KCB":0.086,
    "COOP":0.093,
    "SCOM":0.072,
    "EABL":0.054,
    "KEGN":0.068,
    "NCBA":0.078,
    "KQ":0.000

}


# =========================================================
# RANDOM RETURN
# =========================================================

def random_return(regime):

    r = MARKET_REGIMES.get(regime, MARKET_REGIMES["normal"])

    mu = r["growth"]

    sigma = r["volatility"]

    return random.gauss(mu, sigma)


# =========================================================
# COMPOUND INVESTMENT
# =========================================================

def compound_value(monthly, years, annual_return):

    months = years * 12

    monthly_return = annual_return / 12

    future = 0

    for i in range(months):

        future *= (1 + monthly_return)

        future += monthly

    return future


# =========================================================
# DIVIDEND CALCULATOR
# =========================================================

def dividend_projection(portfolio):

    total = 0

    for asset in portfolio:

        code = asset["code"]

        value = asset["value"]

        y = DIVIDENDS.get(code,0)

        total += value * y

    return total


# =========================================================
# SINGLE SCENARIO
# =========================================================

def simulate_portfolio(portfolio,
                       monthly,
                       years,
                       regime="normal"):

    annual = random_return(regime)

    invested = monthly * 12 * years

    future = compound_value(
        monthly,
        years,
        annual
    )

    dividends = dividend_projection(portfolio)

    return {

        "scenario":regime,

        "invested":invested,

        "portfolio_value":future,

        "profit":future-invested,

        "roi":((future-invested)/invested)*100,

        "annual_return":annual*100,

        "dividends":dividends

    }


# =========================================================
# THREE MARKET SCENARIOS
# =========================================================

def run_all_scenarios(portfolio,
                      monthly,
                      years):

    results={}

    for regime in MARKET_REGIMES:

        results[regime]=simulate_portfolio(

            portfolio,

            monthly,

            years,

            regime

        )

    return results


# =========================================================
# CAGR
# =========================================================

def calculate_cagr(invested,
                   value,
                   years):

    if invested<=0:

        return 0

    return (

        math.pow(value/invested,1/years)-1

    )*100


# =========================================================
# PORTFOLIO HEALTH SCORE
# =========================================================

def portfolio_health(portfolio):

    score=0

    for p in portfolio:

        score += p.get("health_score",75)

    return round(score/len(portfolio),1)