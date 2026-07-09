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
# MARKET REGIME INTELLIGENCE ENGINE
# ==========================================================

def regime_adjustment(asset, mode):
    """
    Adjusts recommendations based on the current
    market regime.
    """

    sector = asset.get("sector", "Unknown")
    dividend = asset.get("dividend_yield", 0)
    beta = asset.get("beta", 1.0)

    # Default
    adjustment = 0
    message = "Neutral positioning."

    # ------------------------------------------------------
    # BULL MARKET
    # ------------------------------------------------------
    if mode == "bull":

        if beta > 1.1:
            adjustment += 8
            message = (
                "Bull market favours higher-beta "
                "growth opportunities."
            )

        elif sector in [
            "Technology",
            "Banking",
            "Telecommunications"
        ]:
            adjustment += 6
            message = (
                "Sector expected to outperform "
                "during expansion."
            )

    # ------------------------------------------------------
    # BEAR MARKET
    # ------------------------------------------------------
    elif mode == "bear":

        if dividend >= 6:
            adjustment += 8
            message = (
                "Strong dividend income improves "
                "defensive positioning."
            )

        elif beta < 0.9:
            adjustment += 6
            message = (
                "Low-beta asset provides downside "
                "protection."
            )

        else:
            adjustment -= 5
            message = (
                "Higher market volatility may "
                "reduce expected returns."
            )

    # ------------------------------------------------------
    # NORMAL MARKET
    # ------------------------------------------------------
    else:

        adjustment += 3

        message = (
            "Balanced market environment."
        )

    return adjustment, message
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
# PORTFOLIO STRENGTHS
# ==========================================================

def portfolio_strengths(portfolio):

    strengths = []

    avg_dividend = statistics.mean(
        a.get("dividend_yield", 0)
        for a in portfolio
    ) if portfolio else 0

    avg_quality = statistics.mean(
        a.get("quality_score", 0)
        for a in portfolio
    ) if portfolio else 0

    avg_beta = statistics.mean(
        a.get("beta", 1)
        for a in portfolio
    ) if portfolio else 1

    if avg_dividend >= 5:
        strengths.append(
            "Strong dividend income generation"
        )

    if avg_quality >= 75:
        strengths.append(
            "High quality company selection"
        )

    if avg_beta < 1:
        strengths.append(
            "Defensive risk profile"
        )

    if not strengths:
        strengths.append(
            "Balanced institutional allocation"
        )

    return strengths 
# ==========================================================
# PORTFOLIO WEAKNESSES
# ==========================================================

def portfolio_weaknesses(portfolio):

    weaknesses = []

    avg_beta = statistics.mean(
        a.get("beta", 1)
        for a in portfolio
    ) if portfolio else 1

    avg_risk = statistics.mean(
        a.get("risk_score", 50)
        for a in portfolio
    ) if portfolio else 50

    if avg_beta > 1.3:
        weaknesses.append(
            "High market sensitivity"
        )

    if avg_risk > 70:
        weaknesses.append(
            "Elevated portfolio risk"
        )

    sectors = set(
        a.get("sector", "Unknown")
        for a in portfolio
    )

    if len(sectors) < 3:
        weaknesses.append(
            "Limited sector diversification"
        )

    return weaknesses
# ==========================================================
# REBALANCING ENGINE
# ==========================================================

def rebalance_advice(portfolio):

    if not portfolio:

        return {
            "required": False,
            "reason": "No portfolio data available.",
            "action": "None"
        }

    largest = max(
        portfolio,
        key=lambda x: x.get(
            "allocation_pct",
            0
        )
    )

    allocation = largest.get(
        "allocation_pct",
        0
    )

    if allocation > 35:

        return {

            "required": True,

            "reason":
            "Single position exceeds "
            "institutional concentration limits.",

            "action":
            f"Reduce exposure to "
            f"{largest.get('asset')}."
        }

    return {

        "required": False,

        "reason":
        "Portfolio appears balanced.",

        "action":
        "No immediate rebalancing required."
    }
# ==========================================================
# INSTITUTIONAL MARKET OUTLOOK
# ==========================================================

def market_outlook(mode, model, portfolio):
    """
    Generates institutional market commentary
    based on market regime and investment model.
    """

    mode = str(mode).lower()
    model = str(model).lower()

    outlook = {}

    # ------------------------------------------------------
    # Market Outlook
    # ------------------------------------------------------
    if mode == "bull":

        outlook["market"] = (
            "Bull market conditions are expected to support "
            "capital appreciation and earnings growth."
        )

    elif mode == "bear":

        outlook["market"] = (
            "Bear market conditions require disciplined "
            "risk management and defensive positioning."
        )

    else:

        outlook["market"] = (
            "Market conditions remain broadly balanced with "
            "moderate return expectations."
        )
    
    # ==========================================================
    # EXECUTIVE SUMMARY
    # ==========================================================
    def executive_summary(summary, analysis):
            """
            Generates an executive summary for the portfolio.
            """

            rating = analysis.get("rating", "N/A")

            roi = summary.get("roi", 0)

            health = analysis.get("health", 0)

            return (
                f"The portfolio achieved an ROI of {roi:.2f}% "
                f"with an institutional rating of {rating}. "
                f"Overall portfolio health stands at "
                f"{health:.1f}/100, indicating "
                f"{analysis.get('risk', 'balanced').lower()} "
                f"investment characteristics."
     )
    
    # ------------------------------------------------------
    # Interest Rates
    # ------------------------------------------------------
    if model in ["dividend", "income"]:

        outlook["interest_rates"] = (
            "Income-oriented strategies remain attractive "
            "while interest rates stay elevated."
        )

    else:

        outlook["interest_rates"] = (
            "Growth investments may become more attractive "
            "as financing conditions improve."
        )

    # ------------------------------------------------------
    # Inflation
    # ------------------------------------------------------
    outlook["inflation"] = (
        "Inflation should continue to influence corporate "
        "earnings and consumer demand."
    )

    # ------------------------------------------------------
    # Dividend Outlook
    # ------------------------------------------------------
    avg_dividend = 0

    if portfolio:

        avg_dividend = sum(
            a.get("dividend_yield", 0)
            for a in portfolio
        ) / len(portfolio)

    if avg_dividend >= 6:

        outlook["dividends"] = (
            "Portfolio provides strong dividend income with "
            "good sustainability."
        )

    elif avg_dividend >= 4:

        outlook["dividends"] = (
            "Dividend income remains healthy with moderate "
            "growth potential."
        )

    else:

        outlook["dividends"] = (
            "Capital appreciation is expected to contribute "
            "more than dividend income."
        )

    # ------------------------------------------------------
    # Overall Investment View
    # ------------------------------------------------------
    if mode == "bull":

        outlook["committee"] = (
            "Investment Committee recommends maintaining "
            "strategic equity exposure while monitoring "
            "valuation risks."
        )

    elif mode == "bear":

        outlook["committee"] = (
            "Investment Committee recommends emphasizing "
            "quality companies, strong cash flows and "
            "defensive sectors."
        )

    else:

        outlook["committee"] = (
            "Investment Committee recommends maintaining "
            "a diversified long-term allocation."
        )

    return outlook
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
        Portfolio breakdown produced by portfolio.py.

    summary : dict
        Portfolio summary from analytics.py.

    mode : str
        Market regime (normal, bull or bear).

    model : str
        Investment model
        (dividend, growth, banking, value or income).

    Returns
    -------
    dict
        Complete AI investment analysis.
    """
    # ------------------------------------------------------
    # Market Intelligence
    # ------------------------------------------------------
    outlook = market_outlook(
        mode,
        model,
        portfolio
    )
     # ------------------------------------------------------
    # Market Intelligence
    # ------------------------------------------------------

    outlook = market_outlook(
        mode,
        model,
        portfolio
    )
    # ------------------------------------------------------
    # Company Recommendations
    # ------------------------------------------------------
    recommendations = []

    for asset in portfolio:

        # Market Regime Adjustment
        regime_bonus, regime_message = regime_adjustment(
            asset,
            mode
        )

        # AI Confidence
        base_confidence = confidence(asset)

        final_confidence = max(
            50,
            min(
                99,
                base_confidence + regime_bonus
            )
        )

        # Recommendation
        rec = recommendation(asset)

        recommendations.append({

            "asset": asset["asset"],

            "code": asset["code"],

            "sector": asset.get("sector", "Unknown"),

            "recommendation": rec,

            "confidence": round(final_confidence, 1),

            "roi": asset.get("roi", 0),

            "risk_score": asset.get("risk_score", 50),

            "dividend_yield": asset.get(
                "dividend_yield",
                0
            ),

            "regime_comment": regime_message

        })
    # ------------------------------------------------------
    # Highest Conviction Investment
    # ------------------------------------------------------
    if recommendations:

        best_pick = max(
            recommendations,
            key=lambda x: (
                x["recommendation"] == "STRONG BUY",
                x["confidence"]
            )
        )

    else:

        best_pick = None

    # ------------------------------------------------------
    # AI Output
    # ------------------------------------------------------
    return {

        "health": analysis.get("health", 0),

        "rating": analysis.get("rating", "N/A"),

        "risk": analysis.get("risk", "UNKNOWN"),

        "risk_score": analysis.get("risk_score", 0),

        "diversification": analysis.get("diversification", 0),

        "dividend_score": analysis.get("dividend_score", 0),

        "market_mode": mode.title(),

        "investment_model": model.title(),

        "message": analysis.get("message", ""),

        "best_pick": best_pick,

        "recommendations": recommendations,

        "companies": len(portfolio),

        "generated": "Institutional AI Engine V2",

        "strengths": portfolio_strengths(portfolio),

        "weaknesses": portfolio_weaknesses(portfolio),

        "rebalance": rebalance_advice(portfolio),

        "executive_summary": executive_summary(
        summary,
        analysis
        ),

        "market_outlook": outlook

    }
