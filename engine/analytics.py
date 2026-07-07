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
