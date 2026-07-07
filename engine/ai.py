"""
==========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
AI Investment Advisor
==========================================================
"""

import statistics


# ==========================================================
# Portfolio Health Score
# ==========================================================

def portfolio_health(returns):

    if not returns:
        return 0

    roi = statistics.mean([r["roi"] for r in returns])
    dividend = statistics.mean([r["dividends"] for r in returns])
    risk = statistics.mean([r["risk_score"] for r in returns])

    score = (
        roi * 0.45 +
        dividend * 0.20 +
        (100 - risk) * 0.35
    )

    return round(score, 2)


# ==========================================================
# Diversification Score
# ==========================================================

def diversification_score(plan):

    sectors = set()

    for asset in plan:
        sectors.add(asset.get("sector", "Unknown"))

    score = min(100, len(sectors) * 20)

    return score


# ==========================================================
# Dividend Sustainability
# ==========================================================

def dividend_score(returns):

    if not returns:
        return 0

    avg = statistics.mean(
        r["dividends"] for r in returns
    )

    return round(min(avg / 1000, 100), 2)


# ==========================================================
# Risk Classification
# ==========================================================

def classify_risk(risk_score):

    if risk_score < 30:
        return "LOW"

    if risk_score < 60:
        return "MEDIUM"

    return "HIGH"


# ==========================================================
# Institutional Rating
# ==========================================================

def institutional_rating(score):

    if score >= 90:
        return "AAA"

    if score >= 80:
        return "AA"

    if score >= 70:
        return "A"

    if score >= 60:
        return "BBB"

    return "BB"


# ==========================================================
# Buy Hold Sell Engine
# ==========================================================

def recommendation(asset):

    roi = asset["roi"]
    risk = asset["risk_score"]

    if roi > 25 and risk < 35:
        return "STRONG BUY"

    if roi > 15:
        return "BUY"

    if roi > 5:
        return "HOLD"

    if roi > 0:
        return "REDUCE"

    return "SELL"


# ==========================================================
# Confidence Score
# ==========================================================

def confidence(asset):

    roi = asset["roi"]
    risk = asset["risk_score"]

    score = max(
        50,
        min(
            99,
            80 + roi / 2 - risk / 4
        )
    )

    return round(score, 1)


# ==========================================================
# Complete AI Analysis
# ==========================================================

def analyze_portfolio(summary, returns, plan):

    health = portfolio_health(returns)

    diversification = diversification_score(plan)

    dividend = dividend_score(returns)

    avg_risk = statistics.mean(
        r["risk_score"] for r in returns
    )

    rating = institutional_rating(health)

    return {

        "health": health,

        "rating": rating,

        "diversification": diversification,

        "dividend_score": dividend,

        "risk_score": round(avg_risk, 2),

        "risk": classify_risk(avg_risk),

        "message": generate_message(
            health,
            diversification,
            avg_risk
        )

    }


# ==========================================================
# AI Commentary
# ==========================================================

def generate_message(
        health,
        diversification,
        risk):

    if health >= 90:

        return (
            "Excellent institutional-quality portfolio. "
            "Suitable for long-term wealth creation with "
            "strong capital appreciation and income generation."
        )

    if health >= 80:

        return (
            "Strong portfolio with good diversification and "
            "healthy risk-adjusted returns."
        )

    if health >= 70:

        return (
            "Balanced portfolio. Consider increasing exposure "
            "to higher quality dividend-paying companies."
        )

    if health >= 60:

        return (
            "Moderate portfolio quality. Rebalancing is "
            "recommended to improve long-term performance."
        )

    return (
        "High-risk portfolio detected. Review allocations "
        "and reduce exposure to volatile securities."
    )
