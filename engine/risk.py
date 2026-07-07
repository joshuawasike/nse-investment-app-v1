"""
==========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Institutional Risk Analytics Engine
==========================================================
"""

import math
import statistics


# ==========================================================
# Portfolio Volatility
# ==========================================================

def volatility(returns):

    """
    Standard deviation of portfolio returns.
    """

    if len(returns) < 2:
        return 0.0

    return round(statistics.stdev(returns), 2)


# ==========================================================
# Average Return
# ==========================================================

def average_return(returns):

    if not returns:
        return 0.0

    return round(statistics.mean(returns), 2)


# ==========================================================
# Sharpe Ratio
# ==========================================================

def sharpe_ratio(returns, risk_free_rate=5.0):

    """
    Calculates the Sharpe Ratio.

    risk_free_rate is expressed as an annual percentage.
    """

    if len(returns) < 2:
        return 0.0

    avg = statistics.mean(returns)

    std = statistics.stdev(returns)

    if std == 0:
        return 0.0

    sharpe = (avg - risk_free_rate) / std

    return round(sharpe, 2)


# ==========================================================
# Maximum Drawdown
# ==========================================================

def maximum_drawdown(values):

    """
    Calculates the largest decline from a previous peak.
    """

    if not values:
        return 0.0

    peak = values[0]
    max_dd = 0

    for value in values:

        if value > peak:
            peak = value

        drawdown = ((peak - value) / peak) * 100

        if drawdown > max_dd:
            max_dd = drawdown

    return round(max_dd, 2)


# ==========================================================
# Value at Risk (Historical Approximation)
# ==========================================================

def value_at_risk(returns, confidence=95):

    """
    Historical VaR approximation.
    """

    if not returns:
        return 0.0

    ordered = sorted(returns)

    index = int((100 - confidence) / 100 * len(ordered))

    index = max(0, min(index, len(ordered) - 1))

    return round(ordered[index], 2)


# ==========================================================
# Risk Classification
# ==========================================================

def classify(volatility_value):

    if volatility_value < 10:
        return "LOW"

    elif volatility_value < 20:
        return "MEDIUM"

    return "HIGH"


# ==========================================================
# Institutional Risk Score
# ==========================================================

def risk_score(volatility_value, drawdown):

    score = 100 - (
        volatility_value * 2 +
        drawdown * 0.5
    )

    score = max(0, min(100, score))

    return round(score, 2)


# ==========================================================
# Downside Risk
# ==========================================================

def downside_risk(returns):

    negatives = [r for r in returns if r < 0]

    if len(negatives) < 2:
        return 0.0

    return round(statistics.stdev(negatives), 2)


# ==========================================================
# Sortino Ratio
# ==========================================================

def sortino_ratio(returns, target_return=0):

    downside = downside_risk(returns)

    if downside == 0:
        return 0.0

    avg = statistics.mean(returns)

    return round((avg - target_return) / downside, 2)


# ==========================================================
# Portfolio Beta (Simplified)
# ==========================================================

def beta(portfolio_returns, market_returns):

    if len(portfolio_returns) != len(market_returns):
        return 1.0

    if len(portfolio_returns) < 2:
        return 1.0

    p_mean = statistics.mean(portfolio_returns)
    m_mean = statistics.mean(market_returns)

    covariance = sum(
        (p - p_mean) * (m - m_mean)
        for p, m in zip(portfolio_returns, market_returns)
    )

    covariance /= (len(portfolio_returns) - 1)

    market_variance = statistics.variance(market_returns)

    if market_variance == 0:
        return 1.0

    return round(covariance / market_variance, 2)


# ==========================================================
# Comprehensive Risk Report
# ==========================================================

def portfolio_risk_report(returns, values):

    vol = volatility(returns)

    dd = maximum_drawdown(values)

    report = {

        "average_return": average_return(returns),

        "volatility": vol,

        "sharpe_ratio": sharpe_ratio(returns),

        "sortino_ratio": sortino_ratio(returns),

        "max_drawdown": dd,

        "value_at_risk": value_at_risk(returns),

        "risk_score": risk_score(vol, dd),

        "classification": classify(vol)

    }

    return report
