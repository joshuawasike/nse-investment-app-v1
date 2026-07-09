"""
=========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Professional Portfolio Analytics Engine
Version 1.0
=========================================================
"""

import math
import numpy as np

def calculate_roi(invested, value):
    if invested <= 0:
        return 0.0
    return round(((value-invested)/invested)*100,2)

def calculate_cagr(invested, value, years):
    if invested<=0 or years<=0 or value<=0:
        return 0.0
    return round((((value/invested)**(1/years))-1)*100,2)

def dividend_yield(dividend_income, portfolio_value):
    if portfolio_value<=0:
        return 0.0
    return round((dividend_income/portfolio_value)*100,2)

def annualized_volatility(returns):
    if len(returns)<2:
        return 0.0
    return round(float(np.std(returns,ddof=1)*math.sqrt(252)*100),2)

def sharpe_ratio(returns,risk_free_rate=0.05):
    if len(returns)<2:
        return 0.0
    excess=np.array(returns)-risk_free_rate/252
    s=np.std(excess,ddof=1)
    if s==0:
        return 0.0
    return round(float(np.mean(excess)/s*math.sqrt(252)),2)

def max_drawdown(values):
    if not values:
        return 0.0
    peak=values[0]
    mdd=0
    for v in values:
        if v>peak:
            peak=v
        dd=(peak-v)/peak if peak else 0
        mdd=max(mdd,dd)
    return round(mdd*100,2)

def portfolio_health(portfolio):
    if not portfolio:
        return 0
    return round(sum(x.get("health_score",75) for x in portfolio)/len(portfolio),1)

def quality_score(portfolio):
    if not portfolio:
        return 0
    return round(sum(x.get("quality_score",75) for x in portfolio)/len(portfolio),1)

def diversification_score(portfolio):
    if not portfolio:
        return 0
    return min(100,len(set(x.get("sector","Unknown") for x in portfolio))*20)

def risk_score(portfolio):
    score=100
    for c in portfolio:
        r=c.get("risk","Medium")
        score-=20 if r=="High" else 10 if r=="Medium" else 5
    return max(score,0)

def institutional_rating(score):
    if score>=95:return "AAA"
    if score>=90:return "AA+"
    if score>=85:return "AA"
    if score>=80:return "A+"
    if score>=75:return "A"
    if score>=70:return "BBB"
    if score>=60:return "BB"
    return "B"

def sector_allocation(portfolio):
    total=len(portfolio)
    if total==0:return {}
    out={}
    for c in portfolio:
        s=c.get("sector","Unknown")
        out[s]=out.get(s,0)+1
    return {k:round(v/total*100,2) for k,v in out.items()}

def portfolio_summary(portfolio,invested,value,dividends,years,returns=None,history=None):
    returns=returns or []
    history=history or [invested,value]
    health=portfolio_health(portfolio)
    return {
        "invested":invested,
        "value":value,
        "profit":round(value-invested,2),
        "roi":calculate_roi(invested,value),
        "cagr":calculate_cagr(invested,value,years),
        "dividend_income":dividends,
        "dividend_yield":dividend_yield(dividends,value),
        "volatility":annualized_volatility(returns),
        "sharpe_ratio":sharpe_ratio(returns),
        "max_drawdown":max_drawdown(history),
        "health_score":health,
        "quality_score":quality_score(portfolio),
        "diversification":diversification_score(portfolio),
        "risk_score":risk_score(portfolio),
        "sector_allocation":sector_allocation(portfolio),
        "institutional_rating":institutional_rating(health)
    }
# ==========================================================
# COMPANY ANALYTICS ENGINE
# ==========================================================

def company_analytics(code, capital):
    """
    Generates institutional analytics for an individual company.
    """

    profiles = {

        "SCOM": {
            "yield": 6.8,
            "growth": 8.5,
            "health": 92,
            "quality": 94,
            "stability": 95,
            "beta": 0.85,
            "policy": "Stable",
            "sector": "Telecommunications",
            "roe": 31.5,
            "pe": 14.2,
            "pb": 3.8,
            "credit": "AA",
            "esg": 89
        },

        "EQTY": {
            "yield": 7.4,
            "growth": 11.2,
            "health": 90,
            "quality": 91,
            "stability": 90,
            "beta": 0.96,
            "policy": "Progressive",
            "sector": "Banking",
            "roe": 24.8,
            "pe": 7.6,
            "pb": 1.4,
            "credit": "AA",
            "esg": 82
        },

        "KCB": {
            "yield": 8.1,
            "growth": 9.5,
            "health": 88,
            "quality": 89,
            "stability": 88,
            "beta": 1.02,
            "policy": "Stable",
            "sector": "Banking",
            "roe": 21.9,
            "pe": 6.8,
            "pb": 1.2,
            "credit": "AA-",
            "esg": 81
        },

        "COOP": {
            "yield": 9.3,
            "growth": 8.8,
            "health": 89,
            "quality": 90,
            "stability": 91,
            "beta": 0.92,
            "policy": "Stable",
            "sector": "Banking",
            "roe": 23.4,
            "pe": 5.9,
            "pb": 1.1,
            "credit": "A+",
            "esg": 79
        },

        "NCBA": {
            "yield": 7.0,
            "growth": 10.5,
            "health": 87,
            "quality": 88,
            "stability": 87,
            "beta": 1.01,
            "policy": "Progressive",
            "sector": "Banking",
            "roe": 19.8,
            "pe": 6.4,
            "pb": 1.0,
            "credit": "A+",
            "esg": 78
        },

        "EABL": {
            "yield": 5.6,
            "growth": 9.8,
            "health": 93,
            "quality": 95,
            "stability": 94,
            "beta": 0.74,
            "policy": "Stable",
            "sector": "Consumer Goods",
            "roe": 28.2,
            "pe": 18.5,
            "pb": 4.2,
            "credit": "AAA",
            "esg": 91
        },

        "KEGN": {
            "yield": 6.2,
            "growth": 5.9,
            "health": 84,
            "quality": 83,
            "stability": 88,
            "beta": 0.68,
            "policy": "Stable",
            "sector": "Energy",
            "roe": 16.8,
            "pe": 8.4,
            "pb": 0.9,
            "credit": "A",
            "esg": 80
        },

        "KQ": {
            "yield": 0.0,
            "growth": 18.0,
            "health": 60,
            "quality": 65,
            "stability": 55,
            "beta": 1.55,
            "policy": "No Dividend",
            "sector": "Transport",
            "roe": -4.8,
            "pe": 0.0,
            "pb": 0.4,
            "credit": "B",
            "esg": 61
        }

    }

    data = profiles.get(code, {})

    return {

        "yield": data.get("yield", 5.0),

        "growth": data.get("growth", 5.0),

        "health": data.get("health", 75),

        "quality": data.get("quality", 75),

        "stability": data.get("stability", 75),

        "income": round(capital * data.get("yield", 5.0) / 100, 2),

        "beta": data.get("beta", 1.0),

        "policy": data.get("policy", "Stable"),

        "sector": data.get("sector", "Unknown"),

        "roe": data.get("roe", 0),

        "pe": data.get("pe", 0),

        "pb": data.get("pb", 0),

        "credit": data.get("credit", "NR"),

        "esg": data.get("esg", 70)

    }
