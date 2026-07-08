"""
=========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Institutional Risk Analytics Engine
Version 2.0
=========================================================

Provides institutional-grade portfolio risk analytics
including volatility, drawdown, Value-at-Risk (VaR),
Expected Shortfall (CVaR), beta, stress testing,
concentration analysis and comprehensive risk reporting.
"""

# ==========================================================
# IMPORTS
# ==========================================================

import math

import numpy as np

# ==========================================================
# ANNUALIZATION CONSTANTS
# ==========================================================

TRADING_DAYS = 252

RISK_FREE_RATE = 0.05

CONFIDENCE_LEVEL = 0.95

# ==========================================================
# RISK CLASSIFICATION THRESHOLDS
# ==========================================================

RISK_THRESHOLDS = {

    "VERY_LOW": 8,

    "LOW": 12,

    "MODERATE": 18,

    "ELEVATED": 25,

    "HIGH": 35

}

# ==========================================================
# STRESS TEST SCENARIOS
# ==========================================================

STRESS_SCENARIOS = {

    "market_correction": -0.10,

    "bear_market": -0.20,

    "financial_crisis": -0.35,

    "interest_rate_shock": -0.08,

    "inflation_shock": -0.12

}

# ==========================================================
# SAFE NUMERIC CONVERSION
# ==========================================================

def safe(value, default=0.0):
    """
    Safely converts a value to float.
    """

    try:

        value = float(value)

        if np.isnan(value):

            return default

        if np.isinf(value):

            return default

        return value

    except Exception:

        return default
# ==========================================================
# CORE RISK STATISTICS
# ==========================================================

def average_return(returns):
    """
    Computes the arithmetic mean of portfolio returns.
    """

    if returns is None or len(returns) == 0:
        return 0.0

    returns = np.asarray(returns, dtype=float)

    return round(float(np.mean(returns)), 4)


# ==========================================================
# PORTFOLIO VOLATILITY
# ==========================================================

def volatility(returns):
    """
    Computes the standard deviation of returns.
    """

    if returns is None or len(returns) < 2:
        return 0.0

    returns = np.asarray(returns, dtype=float)

    return round(float(np.std(returns, ddof=1)), 4)


# ==========================================================
# ANNUALIZED VOLATILITY
# ==========================================================

def annualized_volatility(returns):
    """
    Annualizes daily volatility.
    """

    vol = volatility(returns)

    return round(
        vol * math.sqrt(TRADING_DAYS),
        4
    )


# ==========================================================
# SHARPE RATIO
# ==========================================================

def sharpe_ratio(
    returns,
    risk_free_rate=RISK_FREE_RATE
):
    """
    Calculates the annualized Sharpe Ratio.
    """

    if returns is None or len(returns) < 2:
        return 0.0

    returns = np.asarray(returns, dtype=float)

    excess_returns = (
        returns -
        risk_free_rate / TRADING_DAYS
    )

    std = np.std(
        excess_returns,
        ddof=1
    )

    if std == 0:
        return 0.0

    sharpe = (
        np.mean(excess_returns)
        / std
    ) * math.sqrt(TRADING_DAYS)

    return round(
        float(sharpe),
        3
    )


# ==========================================================
# RETURN DISTRIBUTION
# ==========================================================

def return_distribution(returns):
    """
    Summary statistics for portfolio returns.
    """

    if returns is None or len(returns) == 0:

        return {

            "mean": 0.0,

            "median": 0.0,

            "minimum": 0.0,

            "maximum": 0.0,

            "volatility": 0.0

        }

    returns = np.asarray(
        returns,
        dtype=float
    )

    return {

        "mean":
            round(float(np.mean(returns)), 4),

        "median":
            round(float(np.median(returns)), 4),

        "minimum":
            round(float(np.min(returns)), 4),

        "maximum":
            round(float(np.max(returns)), 4),

        "volatility":
            annualized_volatility(returns)

    }
# ==========================================================
# VALUE AT RISK (VaR)
# ==========================================================

def value_at_risk(
    returns,
    confidence=CONFIDENCE_LEVEL
):
    """
    Historical Value-at-Risk (VaR).

    Returns the loss threshold that is expected
    not to be exceeded with the specified
    confidence level.
    """

    if returns is None or len(returns) == 0:
        return 0.0

    returns = np.asarray(
        returns,
        dtype=float
    )

    percentile = (1.0 - confidence) * 100

    var = np.percentile(
        returns,
        percentile
    )

    return round(float(var), 4)


# ==========================================================
# CONDITIONAL VALUE AT RISK (CVaR)
# ==========================================================

def conditional_value_at_risk(
    returns,
    confidence=CONFIDENCE_LEVEL
):
    """
    Expected Shortfall (CVaR).

    Measures the average loss beyond VaR.
    """

    if returns is None or len(returns) == 0:
        return 0.0

    returns = np.asarray(
        returns,
        dtype=float
    )

    var = value_at_risk(
        returns,
        confidence
    )

    losses = returns[
        returns <= var
    ]

    if len(losses) == 0:
        return float(var)

    return round(
        float(np.mean(losses)),
        4
    )


# ==========================================================
# MAXIMUM DRAWDOWN
# ==========================================================

def maximum_drawdown(values):
    """
    Calculates the maximum portfolio drawdown.
    """

    if values is None or len(values) < 2:
        return 0.0

    values = np.asarray(
        values,
        dtype=float
    )

    running_peak = np.maximum.accumulate(values)

    drawdowns = (
        values - running_peak
    ) / running_peak

    return round(
        float(abs(np.min(drawdowns)) * 100),
        2
    )


# ==========================================================
# DRAWDOWN CURVE
# ==========================================================

def drawdown_curve(values):
    """
    Returns the complete drawdown series.
    """

    if values is None or len(values) == 0:
        return []

    values = np.asarray(
        values,
        dtype=float
    )

    running_peak = np.maximum.accumulate(values)

    drawdowns = (
        values - running_peak
    ) / running_peak

    return [
        round(float(d * 100), 2)
        for d in drawdowns
    ]
# ==========================================================
# DOWNSIDE RISK
# ==========================================================

def downside_risk(returns):
    """
    Computes downside deviation using only
    negative portfolio returns.
    """

    if returns is None or len(returns) < 2:
        return 0.0

    returns = np.asarray(
        returns,
        dtype=float
    )

    downside = returns[
        returns < 0
    ]

    if len(downside) < 2:
        return 0.0

    return round(
        float(np.std(
            downside,
            ddof=1
        )),
        4
    )


# ==========================================================
# SORTINO RATIO
# ==========================================================

def sortino_ratio(
    returns,
    target_return=0.0
):
    """
    Calculates the annualized Sortino Ratio.
    """

    if returns is None or len(returns) < 2:
        return 0.0

    returns = np.asarray(
        returns,
        dtype=float
    )

    downside = downside_risk(returns)

    if downside == 0:
        return 0.0

    excess_return = (
        np.mean(returns) -
        target_return / TRADING_DAYS
    )

    sortino = (
        excess_return /
        downside
    ) * math.sqrt(TRADING_DAYS)

    return round(
        float(sortino),
        3
    )


# ==========================================================
# PORTFOLIO BETA
# ==========================================================

def beta(
    portfolio_returns,
    market_returns
):
    """
    Calculates portfolio beta relative
    to the benchmark market.
    """

    if (
        portfolio_returns is None
        or market_returns is None
    ):
        return 1.0

    if len(portfolio_returns) != len(market_returns):
        return 1.0

    if len(portfolio_returns) < 2:
        return 1.0

    p = np.asarray(
        portfolio_returns,
        dtype=float
    )

    m = np.asarray(
        market_returns,
        dtype=float
    )

    covariance = np.cov(
        p,
        m,
        ddof=1
    )[0][1]

    market_variance = np.var(
        m,
        ddof=1
    )

    if market_variance == 0:
        return 1.0

    return round(
        float(covariance / market_variance),
        3
    )


# ==========================================================
# TRACKING ERROR
# ==========================================================

def tracking_error(
    portfolio_returns,
    benchmark_returns
):
    """
    Measures deviation from benchmark returns.
    """

    if (
        portfolio_returns is None
        or benchmark_returns is None
    ):
        return 0.0

    if len(portfolio_returns) != len(benchmark_returns):
        return 0.0

    diff = (
        np.asarray(portfolio_returns)
        -
        np.asarray(benchmark_returns)
    )

    return round(
        float(
            np.std(
                diff,
                ddof=1
            ) * math.sqrt(TRADING_DAYS)
        ),
        4
    )


# ==========================================================
# INFORMATION RATIO
# ==========================================================

def information_ratio(
    portfolio_returns,
    benchmark_returns
):
    """
    Measures excess return relative
    to tracking error.
    """

    te = tracking_error(
        portfolio_returns,
        benchmark_returns
    )

    if te == 0:
        return 0.0

    active_return = (
        np.mean(portfolio_returns)
        -
        np.mean(benchmark_returns)
    )

    return round(
        float(active_return / te),
        3
    )
# ==========================================================
# CONCENTRATION RISK
# ==========================================================

def concentration_risk(weights):
    """
    Evaluates portfolio concentration using the
    Herfindahl-Hirschman Index (HHI).
    """

    if weights is None or len(weights) == 0:

        return {
            "hhi": 0.0,
            "effective_holdings": 0.0,
            "classification": "UNKNOWN"
        }

    weights = np.asarray(
        weights,
        dtype=float
    )

    total = np.sum(weights)

    if total <= 0:

        return {
            "hhi": 0.0,
            "effective_holdings": 0.0,
            "classification": "UNKNOWN"
        }

    weights = weights / total

    hhi = np.sum(weights ** 2)

    effective_holdings = 1.0 / hhi

    if hhi < 0.10:

        level = "VERY LOW"

    elif hhi < 0.18:

        level = "LOW"

    elif hhi < 0.25:

        level = "MODERATE"

    elif hhi < 0.40:

        level = "HIGH"

    else:

        level = "VERY HIGH"

    return {

        "hhi": round(float(hhi), 4),

        "effective_holdings":
            round(float(effective_holdings), 2),

        "classification": level

    }


# ==========================================================
# LARGEST HOLDING
# ==========================================================

def largest_holding(weights):
    """
    Returns the largest portfolio allocation.
    """

    if weights is None or len(weights) == 0:
        return 0.0

    weights = np.asarray(
        weights,
        dtype=float
    )

    return round(
        float(np.max(weights) * 100),
        2
    )


# ==========================================================
# STRESS TEST ENGINE
# ==========================================================

def stress_test(
    portfolio_value,
    scenario="bear_market"
):
    """
    Applies a predefined stress scenario.
    """

    portfolio_value = safe(portfolio_value)

    shock = STRESS_SCENARIOS.get(
        scenario,
        -0.20
    )

    stressed_value = portfolio_value * (
        1.0 + shock
    )

    loss = portfolio_value - stressed_value

    return {

        "scenario": scenario,

        "shock_pct":
            round(shock * 100, 2),

        "original_value":
            round(portfolio_value, 2),

        "stressed_value":
            round(stressed_value, 2),

        "loss":
            round(loss, 2)

    }


# ==========================================================
# RUN ALL STRESS SCENARIOS
# ==========================================================

def stress_report(portfolio_value):
    """
    Runs every institutional stress scenario.
    """

    report = {}

    for scenario in STRESS_SCENARIOS:

        report[scenario] = stress_test(
            portfolio_value,
            scenario
        )

    return report
# ==========================================================
# INDIVIDUAL RISK CONTRIBUTION
# ==========================================================

def risk_contribution(
    portfolio,
    weights
):
    """
    Estimates each asset's contribution to
    overall portfolio risk.
    """

    if (
        portfolio is None
        or weights is None
        or len(portfolio) == 0
        or len(weights) == 0
    ):
        return []

    weights = np.asarray(
        weights,
        dtype=float
    )

    total = np.sum(weights)

    if total <= 0:
        return []

    weights = weights / total

    contributions = []

    for asset, weight in zip(
        portfolio,
        weights
    ):

        beta = safe(
            asset.get("beta", 1.0),
            1.0
        )

        volatility = safe(
            asset.get("volatility", 0.20),
            0.20
        )

        contribution = (
            weight *
            beta *
            volatility
        )

        contributions.append({

            "asset":
                asset.get("asset", "Unknown"),

            "code":
                asset.get("code", ""),

            "sector":
                asset.get(
                    "sector",
                    "Unknown"
                ),

            "weight":
                round(
                    float(weight * 100),
                    2
                ),

            "beta":
                round(beta, 3),

            "volatility":
                round(
                    volatility * 100,
                    2
                ),

            "risk_contribution":
                round(
                    contribution * 100,
                    3
                )

        })

    contributions.sort(

        key=lambda x:
        x["risk_contribution"],

        reverse=True

    )

    return contributions


# ==========================================================
# TOP RISK CONTRIBUTORS
# ==========================================================

def top_risk_contributors(
    portfolio,
    weights,
    top_n=5
):
    """
    Returns the largest contributors
    to portfolio risk.
    """

    return risk_contribution(
        portfolio,
        weights
    )[:top_n]


# ==========================================================
# SECTOR RISK CONTRIBUTION
# ==========================================================

def sector_risk(
    portfolio,
    weights
):
    """
    Aggregates risk contribution
    by sector.
    """

    contributions = risk_contribution(
        portfolio,
        weights
    )

    sectors = {}

    for asset in contributions:

        sector = asset["sector"]

        sectors[sector] = (
            sectors.get(sector, 0)
            +
            asset["risk_contribution"]
        )

    return {

        sector:
        round(value, 3)

        for sector, value
        in sectors.items()

    }


# ==========================================================
# RISK CONCENTRATION ALERT
# ==========================================================

def concentration_alert(
    portfolio,
    weights
):
    """
    Generates concentration warnings.
    """

    largest = largest_holding(
        weights
    )

    if largest >= 40:

        return (
            "Critical concentration risk. "
            "One asset dominates the portfolio."
        )

    if largest >= 30:

        return (
            "High concentration risk. "
            "Consider reducing the largest holding."
        )

    if largest >= 20:

        return (
            "Moderate concentration detected."
        )

    return (
        "Portfolio concentration appears healthy."
    )
# ==========================================================
# INSTITUTIONAL RISK CLASSIFICATION
# ==========================================================

def classify_risk(score):
    """
    Classifies overall portfolio risk based
    on institutional risk score.
    """

    if score >= 90:
        return "VERY LOW"

    if score >= 80:
        return "LOW"

    if score >= 70:
        return "MODERATE"

    if score >= 60:
        return "ELEVATED"

    if score >= 50:
        return "HIGH"

    return "VERY HIGH"


# ==========================================================
# INSTITUTIONAL RISK RATING
# ==========================================================

def institutional_rating(score):
    """
    Converts numerical score into an
    institutional-style rating.
    """

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
# MASTER RISK SCORE
# ==========================================================

def institutional_risk_score(
    volatility_value,
    drawdown,
    beta_value,
    concentration
):
    """
    Computes the overall institutional
    portfolio risk score.
    """

    score = 100.0

    # -----------------------------------
    # Volatility Penalty
    # -----------------------------------
    score -= volatility_value * 1.20

    # -----------------------------------
    # Drawdown Penalty
    # -----------------------------------
    score -= drawdown * 0.50

    # -----------------------------------
    # Beta Penalty
    # -----------------------------------
    score -= abs(beta_value - 1.0) * 10

    # -----------------------------------
    # Concentration Penalty
    # -----------------------------------
    score -= concentration * 30

    score = max(
        0,
        min(100, score)
    )

    return round(score, 2)


# ==========================================================
# RISK INTERPRETATION
# ==========================================================

def risk_commentary(score):
    """
    Generates institutional commentary
    for the portfolio risk profile.
    """

    if score >= 90:

        return (
            "Excellent institutional-quality risk profile. "
            "Portfolio demonstrates strong diversification "
            "and conservative risk management."
        )

    if score >= 80:

        return (
            "Healthy risk profile with good diversification "
            "and acceptable market exposure."
        )

    if score >= 70:

        return (
            "Balanced portfolio with moderate investment risk."
        )

    if score >= 60:

        return (
            "Elevated risk detected. Portfolio rebalancing "
            "should be considered."
        )

    if score >= 50:

        return (
            "High portfolio risk. Diversification and "
            "risk reduction are recommended."
        )

    return (
        "Very high institutional risk detected. Immediate "
        "portfolio review is recommended."
    )


# ==========================================================
# RISK DASHBOARD SUMMARY
# ==========================================================

def risk_dashboard(
    volatility_value,
    drawdown,
    beta_value,
    concentration
):
    """
    Produces a dashboard-ready institutional
    risk summary.
    """

    score = institutional_risk_score(
        volatility_value,
        drawdown,
        beta_value,
        concentration
    )

    return {

        "risk_score": score,

        "classification":
            classify_risk(score),

        "institutional_rating":
            institutional_rating(score),

        "commentary":
            risk_commentary(score)

    }
# ==========================================================
# MASTER PORTFOLIO RISK REPORT
# ==========================================================

def portfolio_risk_report(
    portfolio,
    weights,
    returns,
    values,
    market_returns=None
):
    """
    Generates a complete institutional
    portfolio risk report.
    """

    # ------------------------------------------------------
    # Core Statistics
    # ------------------------------------------------------
    avg_return = average_return(returns)

    vol = annualized_volatility(returns)

    sharpe = sharpe_ratio(returns)

    sortino = sortino_ratio(returns)

    var95 = value_at_risk(returns)

    cvar95 = conditional_value_at_risk(returns)

    drawdown = maximum_drawdown(values)

    # ------------------------------------------------------
    # Benchmark Risk
    # ------------------------------------------------------
    if market_returns is None:

        beta_value = 1.0

        tracking = 0.0

        info_ratio = 0.0

    else:

        beta_value = beta(
            returns,
            market_returns
        )

        tracking = tracking_error(
            returns,
            market_returns
        )

        info_ratio = information_ratio(
            returns,
            market_returns
        )

    # ------------------------------------------------------
    # Concentration
    # ------------------------------------------------------
    concentration = concentration_risk(weights)

    # ------------------------------------------------------
    # Institutional Risk Score
    # ------------------------------------------------------
    dashboard = risk_dashboard(

        vol,

        drawdown,

        beta_value,

        concentration["hhi"]

    )

    # ------------------------------------------------------
    # Final Report
    # ------------------------------------------------------
    report = {

        # Performance
        "average_return": avg_return,

        "volatility": vol,

        "sharpe_ratio": sharpe,

        "sortino_ratio": sortino,

        # Downside Risk
        "value_at_risk": var95,

        "conditional_value_at_risk": cvar95,

        "maximum_drawdown": drawdown,

        # Market Risk
        "beta": beta_value,

        "tracking_error": tracking,

        "information_ratio": info_ratio,

        # Concentration
        "concentration": concentration,

        "largest_holding":
            largest_holding(weights),

        "concentration_alert":
            concentration_alert(
                portfolio,
                weights
            ),

        # Risk Contribution
        "risk_contribution":
            risk_contribution(
                portfolio,
                weights
            ),

        "top_risk_contributors":
            top_risk_contributors(
                portfolio,
                weights
            ),

        "sector_risk":
            sector_risk(
                portfolio,
                weights
            ),

        # Stress Testing
        "stress_tests":
            stress_report(
                values[-1]
                if len(values)
                else 0
            ),

        # Dashboard
        "risk_score":
            dashboard["risk_score"],

        "classification":
            dashboard["classification"],

        "institutional_rating":
            dashboard["institutional_rating"],

        "commentary":
            dashboard["commentary"]

    }

    return report
