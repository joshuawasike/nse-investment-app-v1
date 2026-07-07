"""
=========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform

Portfolio Analytics Engine

This module calculates professional investment
performance metrics for institutional portfolios.

Metrics

• ROI
• CAGR
• Dividend Yield
• Portfolio Health
• Diversification
• Income Score
• Growth Score
• Risk Score
• Institutional Rating

=========================================================
"""

import math


# ==========================================================
# RETURN ON INVESTMENT
# ==========================================================

def calculate_roi(invested, value):

    if invested <= 0:
        return 0

    return round(((value - invested) / invested) * 100, 2)


# ==========================================================
# CAGR
# ==========================================================

def calculate_cagr(invested, value, years):

    if invested <= 0 or years <= 0:
        return 0

    cagr = (value / invested) ** (1 / years) - 1

    return round(cagr * 100, 2)


# ==========================================================
# ANNUAL DIVIDEND YIELD
# ==========================================================

def dividend_yield(dividend_income, portfolio_value):

    if portfolio_value <= 0:
        return 0

    return round((dividend_income / portfolio_value) * 100, 2)


# ==========================================================
# PORTFOLIO HEALTH SCORE
# ==========================================================

def portfolio_health(portfolio):

    if not portfolio:
        return 0

    total = sum(
        company.get("health_score", 75)
        for company in portfolio
    )

    return round(total / len(portfolio), 1)


# ==========================================================
# QUALITY SCORE
# ==========================================================

def quality_score(portfolio):

    if not portfolio:
        return 0

    total = sum(
        company.get("quality_score", 75)
        for company in portfolio
    )

    return round(total / len(portfolio), 1)


# ==========================================================
# DIVERSIFICATION SCORE
# ==========================================================

def diversification_score(portfolio):

    if not portfolio:
        return 0

    sectors = set()

    for company in portfolio:
        sectors.add(company["sector"])

    score = min(100, len(sectors) * 20)

    return score


# ==========================================================
# DIVIDEND INCOME SCORE
# ==========================================================

def income_score(portfolio):

    if not portfolio:
        return 0

    avg = sum(
        company["dividend_yield"]
        for company in portfolio
    ) / len(portfolio)

    return round(min(avg * 10, 100), 1)


# ==========================================================
# GROWTH SCORE
# ==========================================================

def growth_score(portfolio):

    if not portfolio:
        return 0

    avg = sum(
        company["roe"]
        for company in portfolio
    ) / len(portfolio)

    return round(min(avg * 4, 100), 1)


# ==========================================================
# RISK SCORE
# ==========================================================

def risk_score(portfolio):

    if not portfolio:
        return 0

    score = 100

    for company in portfolio:

        risk = company.get("risk", "Medium")

        if risk == "High":
            score -= 20

        elif risk == "Medium":
            score -= 10

        else:
            score -= 5

    return max(score, 0)


# ==========================================================
# INSTITUTIONAL RATING
# ==========================================================

def institutional_rating(score):

    if score >= 95:
        return "AAA"

    if score >= 90:
        return "AA+"

    if score >= 85:
        return "AA"

    if score >= 80:
        return "A+"

    if score >= 75:
        return "A"

    if score >= 70:
        return "BBB"

    if score >= 60:
        return "BB"

    return "B"


# ==========================================================
# COMPLETE ANALYTICS
# ==========================================================

def portfolio_analytics(
    portfolio,
    invested,
    value,
    dividends,
    years
):

    roi = calculate_roi(invested, value)

    cagr = calculate_cagr(
        invested,
        value,
        years
    )

    health = portfolio_health(portfolio)

    quality = quality_score(portfolio)

    diversification = diversification_score(
        portfolio
    )

    income = income_score(portfolio)

    growth = growth_score(portfolio)

    risk = risk_score(portfolio)

    rating = institutional_rating(health)

    return {

        "invested": invested,

        "value": value,

        "profit": value - invested,

        "roi": roi,

        "cagr": cagr,

        "dividend_income": dividends,

        "dividend_yield":
            dividend_yield(
                dividends,
                value
            ),

        "health_score": health,

        "quality_score": quality,

        "diversification": diversification,

        "income_score": income,

        "growth_score": growth,

        "risk_score": risk,

        "institutional_rating": rating

    }
