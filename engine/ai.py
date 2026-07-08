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
# INSTITUTIONAL RECOMMENDATION ENGINE
# ==========================================================

def recommendation(asset):
    """
    Generates institutional BUY/HOLD/SELL recommendations
    using multiple financial quality indicators.
    """

    roi = asset.get("roi", 0)

    risk = asset.get("risk_score", 50)

    dividend = asset.get("dividend_yield", 0)

    quality = asset.get("quality_score", 50)

    health = asset.get("dividend_health", 50)

    beta = asset.get("beta", 1.0)

    roe = asset.get("roe", 0)

    pe = asset.get("pe", 20)

    esg = asset.get("esg", 50)

    credit = str(asset.get("credit", "BBB"))

    score = 0

    # ---------------------------------------
    # ROI
    # ---------------------------------------
    if roi >= 25:
        score += 20
    elif roi >= 15:
        score += 15
    elif roi >= 5:
        score += 10

    # ---------------------------------------
    # Dividend Yield
    # ---------------------------------------
    if dividend >= 8:
        score += 15
    elif dividend >= 5:
        score += 10
    elif dividend >= 3:
        score += 5

    # ---------------------------------------
    # Dividend Health
    # ---------------------------------------
    score += health * 0.10

    # ---------------------------------------
    # Company Quality
    # ---------------------------------------
    score += quality * 0.20

    # ---------------------------------------
    # ROE
    # ---------------------------------------
    if roe >= 20:
        score += 15
    elif roe >= 15:
        score += 10
    elif roe >= 10:
        score += 5

    # ---------------------------------------
    # Beta (lower preferred)
    # ---------------------------------------
    if beta < 0.8:
        score += 10
    elif beta < 1.2:
        score += 6

    # ---------------------------------------
    # Valuation
    # ---------------------------------------
    if pe < 10:
        score += 10
    elif pe < 18:
        score += 6

    # ---------------------------------------
    # ESG
    # ---------------------------------------
    score += esg * 0.05

    # ---------------------------------------
    # Credit Rating
    # ---------------------------------------
    if credit in ["AAA", "AA+", "AA"]:
        score += 10

    elif credit in ["A+", "A"]:
        score += 7

    elif credit == "BBB":
        score += 4

    # ---------------------------------------
    # Risk Penalty
    # ---------------------------------------
    score -= risk * 0.20

    # ---------------------------------------
    # Final Recommendation
    # ---------------------------------------
    if score >= 80:
        return "STRONG BUY"

    if score >= 65:
        return "BUY"

    if score >= 50:
        return "HOLD"

    if score >= 35:
        return "REDUCE"

    return "SELL"


# ==========================================================
# AI CONFIDENCE ENGINE
# ==========================================================

def confidence(asset):
    """
    AI confidence level for each recommendation.
    """

    quality = asset.get("quality_score", 50)

    health = asset.get("dividend_health", 50)

    risk = asset.get("risk_score", 50)

    roi = asset.get("roi", 0)

    beta = asset.get("beta", 1.0)

    score = (
        quality * 0.35
        + health * 0.25
        + roi * 0.60
        - risk * 0.20
        - abs(beta - 1.0) * 10
    )

    score = max(50, min(score, 99))

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
# ==========================================================
# MASTER AI INVESTMENT ADVISOR
# ==========================================================

def investment_advisor(
    portfolio,
    summary,
    mode,
    model
):
    """
    Master AI engine for institutional investment advice.

    Parameters
    ----------
    portfolio : list
        Portfolio breakdown produced by portfolio.py

    summary : dict
        Portfolio summary from analytics.py

    mode : str
        normal / bull / bear

    model : str
        dividend / growth / banking / value / income

    Returns
    -------
    dict
        Complete AI analysis.
    """

    # ------------------------------------------------------
    # Overall Portfolio Analysis
    # ------------------------------------------------------
    analysis = analyze_portfolio(
        summary,
        portfolio,
        portfolio
    )

    # ------------------------------------------------------
    # Company Recommendations
    # ------------------------------------------------------
    recommendations = []

    for asset in portfolio:

        rec = recommendation(asset)

        conf = confidence(asset)

        recommendations.append({

            "asset": asset["asset"],

            "code": asset["code"],

            "sector": asset.get("sector", "Unknown"),

            "recommendation": rec,

            "confidence": conf,

            "roi": asset.get("roi", 0),

            "risk_score": asset.get("risk_score", 50),

            "dividend_yield": asset.get(
                "dividend_yield",
                0
            )

        })

    # ------------------------------------------------------
    # Highest Conviction Investment
    # ------------------------------------------------------
    if recommendations:

        best_pick = max(
            recommendations,
            key=lambda x: x["confidence"]
        )

    else:

        best_pick = None

    # ------------------------------------------------------
    # AI Output
    # ------------------------------------------------------
    return {

        "health": analysis["health"],

        "rating": analysis["rating"],

        "risk": analysis["risk"],

        "risk_score": analysis["risk_score"],

        "diversification": analysis["diversification"],

        "dividend_score": analysis["dividend_score"],

        "market_mode": mode.title(),

        "investment_model": model.title(),

        "message": analysis["message"],

        "best_pick": best_pick,

        "recommendations": recommendations

    }
