"""
=========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Institutional Simulation Engine
Version 2.0
=========================================================

This module is responsible for:

• Market simulation
• Economic regime modelling
• Monte Carlo path generation
• Institutional asset allocation
• Dividend forecasting
• Corporate actions
• Portfolio growth simulation
"""

# =========================================================
# STANDARD LIBRARIES
# =========================================================

from copy import deepcopy

# =========================================================
# DATA SCIENCE
# =========================================================

import numpy as np

# =========================================================
# RESEARCH ENGINE
# =========================================================

from engine.research import (
    ASSETS,
    DIVIDEND_DATABASE,
    get_market_stats,
    get_model_assets,
    estimate_dividend_yields
)

# =========================================================
# CORPORATE ACTIONS
# =========================================================

from engine.corporate_actions import (
    CORPORATE_ACTIONS,
    apply_corporate_actions
)

# =========================================================
# PORTFOLIO ENGINE
# =========================================================

from engine.portfolio import (
    build_portfolio,
    build_investment_plan,
    build_returns_table
)

# =========================================================
# ANALYTICS ENGINE
# =========================================================

from engine.analytics import (
    portfolio_summary
)

# =========================================================
# RISK ENGINE
# =========================================================

from engine.risk import (
    portfolio_risk_report
)

# =========================================================
# AI ENGINE
# =========================================================

from engine.ai import (
    investment_advisor
)

# =========================================================
# RETIREMENT ENGINE
# =========================================================

from engine.retirement import (
    retirement_projection
)

# =========================================================
# REPORTING ENGINE
# =========================================================

from engine.reports import (
    chart
)
# =========================================================
# MODEL CONFIGURATION
# =========================================================

MODEL_PARAMETERS = {

    "dividend": {
        "drift": 0.0035,
        "volatility": 0.012,
        "momentum": 0.60
    },

    "growth": {
        "drift": 0.0060,
        "volatility": 0.022,
        "momentum": 1.10
    },

    "banking": {
        "drift": 0.0045,
        "volatility": 0.016,
        "momentum": 0.80
    },

    "value": {
        "drift": 0.0040,
        "volatility": 0.015,
        "momentum": 0.75
    },

    "income": {
        "drift": 0.0038,
        "volatility": 0.013,
        "momentum": 0.70
    }

}

# =========================================================
# SIMULATION SETTINGS
# =========================================================

TRADING_DAYS = 252
MONTHS_PER_YEAR = 12
SIMULATION_PERIODS = 300

RISK_FREE_RATE = 0.05
INFLATION_RATE = 0.05

MIN_WEIGHT = 0.03
MAX_WEIGHT = 0.40

MIN_RETURN = -0.15
MAX_RETURN = 0.18

EXTREME_EVENT_PROBABILITY = 0.015
# =========================================================
# ECONOMIC REGIME ENGINE
# =========================================================

ECONOMIC_REGIMES = {

    # =====================================================
    # NORMAL MARKET
    # =====================================================
    "normal": {

        "name": "Normal Market",

        # Market Behaviour
        "drift_multiplier": 1.00,
        "alpha": 0.0000,
        "volatility_multiplier": 1.00,
        "momentum_multiplier": 1.00,

        # Income
        "dividend_multiplier": 1.00,
        "earnings_multiplier": 1.00,

        # Stress
        "default_probability": 0.002,
        "shock_probability": 0.015,

        # Portfolio Limits
        "max_drawdown": 0.15,

        # Sector Performance
        "sector": {

            "Banking": 1.00,
            "Telecom": 1.00,
            "Consumer": 1.00,
            "Utilities": 1.00,
            "Energy": 1.00,
            "Insurance": 1.00,
            "Manufacturing": 1.00,
            "Agriculture": 1.00,
            "Investment": 1.00,
            "REIT": 1.00,
            "Airline": 1.00

        }

    },

    # =====================================================
    # BULL MARKET
    # =====================================================
    "bull": {

        "name": "Bull Market",

        "drift_multiplier": 1.12,
        "alpha": 0.0020,
        "volatility_multiplier": 0.80,
        "momentum_multiplier": 1.20,

        "dividend_multiplier": 1.15,
        "earnings_multiplier": 1.15,

        "default_probability": 0.001,
        "shock_probability": 0.010,

        "max_drawdown": 0.10,

        "sector": {

            "Banking": 1.20,
            "Telecom": 1.12,
            "Consumer": 1.15,
            "Utilities": 1.00,
            "Energy": 1.12,
            "Insurance": 1.18,
            "Manufacturing": 1.15,
            "Agriculture": 1.08,
            "Investment": 1.25,
            "REIT": 1.10,
            "Airline": 1.50

        }

    },

    # =====================================================
    # BEAR MARKET
    # =====================================================
    "bear": {

        "name": "Bear Market",

        "drift_multiplier": 0.90,
        "alpha": -0.0020,
        "volatility_multiplier": 1.55,
        "momentum_multiplier": 0.70,

        "dividend_multiplier": 0.82,
        "earnings_multiplier": 0.85,

        "default_probability": 0.015,
        "shock_probability": 0.030,

        "max_drawdown": 0.35,

        "sector": {

            "Banking": 0.75,
            "Telecom": 0.95,
            "Consumer": 0.82,
            "Utilities": 1.05,
            "Energy": 0.80,
            "Insurance": 0.78,
            "Manufacturing": 0.70,
            "Agriculture": 0.95,
            "Investment": 0.72,
            "REIT": 0.80,
            "Airline": 0.30

        }

    }

}

# =========================================================
# HELPER
# =========================================================

def get_regime(mode):
    """
    Returns the selected economic regime.
    Defaults to Normal Market.
    """
    return ECONOMIC_REGIMES.get(
        mode.lower(),
        ECONOMIC_REGIMES["normal"]
    )
# =========================================================
# INSTITUTIONAL MARKET GENERATOR
# =========================================================

def generate_market(mode, model):
    """
    Generates institutional Monte Carlo market returns
    using historical NSE statistics and the selected
    economic regime.

    Parameters
    ----------
    mode : str
        normal, bull or bear

    model : str
        dividend, growth, banking,
        value or income

    Returns
    -------
    numpy.ndarray
        Simulated monthly returns
        (assets × periods)
    """

    # -----------------------------------------------------
    # MODEL PARAMETERS
    # -----------------------------------------------------
    params = MODEL_PARAMETERS.get(
        model,
        MODEL_PARAMETERS["dividend"]
    )

    drift = params["drift"]
    volatility = params["volatility"]
    momentum = params["momentum"]

    # -----------------------------------------------------
    # ECONOMIC REGIME
    # -----------------------------------------------------
    regime = get_regime(mode)

    # -----------------------------------------------------
    # HISTORICAL MARKET DATA
    # -----------------------------------------------------
    stats = get_market_stats()

    if stats is None:

        return np.random.normal(

            drift,

            volatility,

            (
                len(ASSETS),
                SIMULATION_PERIODS
            )

        )

    mu = stats["mu"].copy()
    sigma = stats["sigma"].copy()
    cov = stats["cov"].copy()

    # -----------------------------------------------------
    # MATCH AVAILABLE NSE COMPANIES
    # -----------------------------------------------------
    codes = [asset[1] for asset in ASSETS]

    available = [

        code

        for code in codes

        if (
            code in mu.index
            and
            code in sigma.index
            and
            code in cov.index
        )

    ]

    if len(available) < 2:

        return np.random.normal(

            drift,

            volatility,

            (
                len(ASSETS),
                SIMULATION_PERIODS
            )

        )

    mu = mu.loc[available]

    sigma = sigma.loc[available]

    cov = cov.loc[
        available,
        available
    ]

    # -----------------------------------------------------
    # SECTOR ADJUSTMENTS
    # -----------------------------------------------------
    sector_factor = []

    for code in available:

        profile = DIVIDEND_DATABASE.get(code, {})

        sector = profile.get(
            "sector",
            "Banking"
        )

        sector_factor.append(

            regime["sector"].get(
                sector,
                1.0
            )

        )

    sector_factor = np.array(sector_factor)

    # -----------------------------------------------------
    # EXPECTED RETURNS
    # -----------------------------------------------------
    mu = (

        mu

        * regime["drift_multiplier"]

        * sector_factor

    ) + regime["alpha"]

    mu = np.clip(

        mu,

        -0.02,

        0.02

    )

    # -----------------------------------------------------
    # VOLATILITY
    # -----------------------------------------------------
    sigma *= np.sqrt(

        regime["volatility_multiplier"]

    )

    cov *= regime["volatility_multiplier"]

    # -----------------------------------------------------
    # POSITIVE DEFINITE COVARIANCE
    # -----------------------------------------------------
    cov += np.eye(len(cov)) * 1e-8

    try:

        chol = np.linalg.cholesky(cov)

    except np.linalg.LinAlgError:

        eigvals, eigvecs = np.linalg.eigh(cov)

        eigvals[eigvals < 1e-8] = 1e-8

        cov = (

            eigvecs

            @ np.diag(eigvals)

            @ eigvecs.T

        )

        chol = np.linalg.cholesky(cov)

    # -----------------------------------------------------
    # FAT-TAIL SHOCKS
    # -----------------------------------------------------
    shocks = np.random.standard_t(

        df=6,

        size=(

            len(mu),

            SIMULATION_PERIODS

        )

    )

    correlated = chol @ shocks

    # -----------------------------------------------------
    # MOMENTUM PROCESS
    # -----------------------------------------------------
    phi = np.clip(

        momentum

        * regime["momentum_multiplier"],

        0.15,

        0.98

    )

    trend = np.zeros_like(correlated)

    for t in range(1, SIMULATION_PERIODS):

        trend[:, t] = (

            phi * trend[:, t - 1]

            + correlated[:, t]

        )

    # -----------------------------------------------------
    # FINAL RETURNS
    # -----------------------------------------------------
    returns = mu.values[:, None] + trend

    # -----------------------------------------------------
    # MATCH HISTORICAL VOLATILITY
    # -----------------------------------------------------
    current_std = np.std(

        returns,

        axis=1,

        keepdims=True

    )

    current_std[current_std == 0] = 1e-9

    target_std = sigma.values[:, None]

    returns *= (

        target_std

        / current_std

    )

    # -----------------------------------------------------
    # EXTREME EVENTS
    # -----------------------------------------------------
    disaster = (

        np.random.rand(

            len(mu),

            SIMULATION_PERIODS

        )

        < regime["shock_probability"]

    )

    if mode == "bull":

        shock = np.random.uniform(

            -0.04,

            -0.02,

            disaster.shape

        )

    elif mode == "bear":

        shock = np.random.uniform(

            -0.12,

            -0.05,

            disaster.shape

        )

    else:

        shock = np.random.uniform(

            -0.08,

            -0.03,

            disaster.shape

        )

    returns[disaster] += shock[disaster]

    # -----------------------------------------------------
    # SAFETY LIMITS
    # -----------------------------------------------------
    returns = np.clip(

        returns,

        MIN_RETURN,

        MAX_RETURN

    )

    # -----------------------------------------------------
    # PAD IF REQUIRED
    # -----------------------------------------------------
    if len(returns) < len(ASSETS):

        extra = np.random.normal(

            drift,

            volatility,

            (

                len(ASSETS) - len(returns),

                SIMULATION_PERIODS

            )

        )

        returns = np.vstack([

            returns,

            extra

        ])

    return returns[:len(ASSETS)]
# =========================================================
# INSTITUTIONAL ALLOCATION ENGINE
# =========================================================

def institutional_allocator(returns, mode):
    """
    Builds an institutional portfolio using
    risk-adjusted expected returns.

    Parameters
    ----------
    returns : ndarray
        Simulated asset returns.

    mode : str
        Economic regime.

    Returns
    -------
    ndarray
        Portfolio weights.
    """

    mean = np.mean(returns, axis=1)

    volatility = np.std(returns, axis=1) + 1e-9

    sharpe = mean / volatility

    score = sharpe.copy()

    # -----------------------------------------------------
    # ECONOMIC REGIME TILT
    # -----------------------------------------------------
    if mode == "bull":

        score += mean * 15

    elif mode == "bear":

        score -= volatility * 4

    # -----------------------------------------------------
    # SOFTMAX NORMALIZATION
    # -----------------------------------------------------
    score = score - np.max(score)

    weights = np.exp(score)

    weights /= np.sum(weights)

    # -----------------------------------------------------
    # CONCENTRATION LIMITS
    # -----------------------------------------------------
    weights = np.clip(

        weights,

        MIN_WEIGHT,

        MAX_WEIGHT

    )

    weights /= np.sum(weights)

    return weights


# =========================================================
# MODEL BIAS ENGINE
# =========================================================

MODEL_TARGETS = {

    "dividend": np.array([
        0.20, 0.18, 0.15, 0.10,
        0.15, 0.12, 0.08, 0.02
    ]),

    "growth": np.array([
        0.08, 0.08, 0.08, 0.25,
        0.08, 0.08, 0.10, 0.25
    ]),

    "banking": np.array([
        0.25, 0.22, 0.20, 0.05,
        0.05, 0.05, 0.15, 0.03
    ]),

    "value": np.array([
        0.08, 0.08, 0.08, 0.05,
        0.12, 0.20, 0.12, 0.27
    ]),

    "income": np.array([
        0.10, 0.15, 0.15, 0.10,
        0.25, 0.15, 0.08, 0.02
    ])

}


def apply_model_bias(weights, model):
    """
    Tilts optimized weights towards
    the selected investment model.
    """

    weights = np.array(weights, dtype=float)

    target = MODEL_TARGETS.get(model)

    if target is None:

        return weights / np.sum(weights)

    # ---------------------------------------------
    # Match portfolio size automatically
    # ---------------------------------------------
    if len(target) != len(weights):

        if len(target) > len(weights):

            target = target[:len(weights)]

        else:

            extra = np.repeat(

                1.0 / len(weights),

                len(weights) - len(target)

            )

            target = np.concatenate([

                target,

                extra

            ])

    target = target / np.sum(target)

    # ---------------------------------------------
    # Blend optimizer with strategic model
    # ---------------------------------------------
    weights = (

        0.30 * weights

        +

        0.70 * target

    )

    weights /= np.sum(weights)

    return weights


# =========================================================
# PORTFOLIO REBALANCER
# =========================================================

def rebalance_portfolio(returns, mode, model):
    """
    Creates the final institutional allocation.
    """

    weights = institutional_allocator(

        returns,

        mode

    )

    weights = apply_model_bias(

        weights,

        model

    )

    weights = np.clip(

        weights,

        MIN_WEIGHT,

        MAX_WEIGHT

    )

    weights /= np.sum(weights)

    return weights   
# =========================================================
# INSTITUTIONAL PORTFOLIO SIMULATION ENGINE
# =========================================================

def simulate(
    monthly,
    years,
    mode="normal",
    model="dividend"
):
    """
    Main institutional simulation engine.

    Parameters
    ----------
    monthly : float
        Monthly investment.

    years : int
        Investment period.

    mode : str
        normal / bull / bear

    model : str
        dividend / growth / banking /
        value / income

    Returns
    -------
    dict
    """

    # -----------------------------------------------------
    # SELECT MODEL ASSETS
    # -----------------------------------------------------
    assets = get_model_assets(model)

    if len(assets) == 0:
        assets = ASSETS

    # -----------------------------------------------------
    # GENERATE MARKET
    # -----------------------------------------------------
    market = generate_market(
        mode=mode,
        model=model
    )

    # -----------------------------------------------------
    # Match market to selected assets
    # -----------------------------------------------------
    all_codes = [a[1] for a in ASSETS]

    indexes = []

    for asset in assets:

        try:

            indexes.append(
                all_codes.index(asset[1])
            )

        except ValueError:
            pass

    if len(indexes) == 0:

        indexes = list(range(len(ASSETS)))

        assets = ASSETS

    returns = market[indexes]

    # -----------------------------------------------------
    # BUILD PORTFOLIO
    # -----------------------------------------------------
    weights = rebalance_portfolio(

        returns,

        mode,

        model

    )

    # -----------------------------------------------------
    # INVESTMENT SETTINGS
    # -----------------------------------------------------
    months = years * 12

    invested = monthly * months

    capital = np.zeros(len(weights))

    dividends = np.zeros(len(weights))

    curve = []

    nav = 0.0
# =========================================================
# MONTHLY INVESTMENT ENGINE
# =========================================================

    regime = get_regime(mode)

    regime_dividend = regime["dividend_multiplier"]

    yield_table = estimate_dividend_yields(
        mode,
        model
    )

    # -----------------------------------------------------
    # MONTHLY LOOP
    # -----------------------------------------------------
    for month in range(months):

        column = month % returns.shape[1]

        # -------------------------------------------------
        # YEARLY REBALANCING
        # -------------------------------------------------
        if month > 0 and month % 12 == 0:

            weights = rebalance_portfolio(

                returns,

                mode,

                model

            )

        # -------------------------------------------------
        # PORTFOLIO RETURN
        # -------------------------------------------------
        portfolio_return = np.dot(

            weights,

            returns[:, column]

        )

        if mode == "bull":

            portfolio_return = np.clip(
                portfolio_return,
                -0.03,
                0.08
            )

        elif mode == "bear":

            portfolio_return = np.clip(
                portfolio_return,
                -0.05,
                0.03
            )

        else:

            portfolio_return = np.clip(
                portfolio_return,
                -0.04,
                0.05
            )

        # -------------------------------------------------
        # UPDATE NAV
        # -------------------------------------------------
        nav *= (1 + portfolio_return)

        nav += monthly

        curve.append(nav)

        # -------------------------------------------------
        # MONTHLY CONTRIBUTION
        # -------------------------------------------------
        allocation = monthly * weights

        capital += allocation

        # -------------------------------------------------
        # GROW EACH ASSET
        # -------------------------------------------------
        capital *= (

            1 +

            returns[:, column]

        )

        # -------------------------------------------------
        # CURRENT MONTH
        # -------------------------------------------------
        payment_month = (month % 12) + 1

        # -------------------------------------------------
        # DIVIDEND ENGINE
        # -------------------------------------------------
        for i, asset in enumerate(assets):

            code = asset[1]

            profile = DIVIDEND_DATABASE.get(
                code,
                {}
            )

            payment_schedule = profile.get(
                "months",
                []
            )

            years_elapsed = month / 12

            dividend_yield = forecast_dividend_yield(

                code,

                years_elapsed,

                mode

            )

            payout = profile.get(
                "payout",
                0.40
            )

            if payment_month in payment_schedule:

                payments = max(
                    len(payment_schedule),
                    1
                )

                dividend = (

                    capital[i]

                    * dividend_yield

                    * payout

                    * regime_dividend

                    / payments

                )

                capital[i], bonus = apply_corporate_actions(

                    capital[i],

                    code

                )

                dividends[i] += (

                    dividend

                    + bonus

                )
# =========================================================
# PERFORMANCE ANALYTICS
# =========================================================

    # -----------------------------------------------------
    # FINAL PORTFOLIO VALUE
    # -----------------------------------------------------
    final_nav = float(curve[-1])

    total_dividends = float(np.sum(dividends))

    portfolio_value = final_nav + total_dividends

    # -----------------------------------------------------
    # MONTHLY RETURNS
    # -----------------------------------------------------
    curve_array = np.array(curve)

    if len(curve_array) > 1:

        monthly_returns = np.diff(curve_array) / np.maximum(
            curve_array[:-1],
            1
        )

    else:

        monthly_returns = np.array([])

    # -----------------------------------------------------
    # BUILD PORTFOLIO BREAKDOWN
    # -----------------------------------------------------
    portfolio = build_portfolio(

        assets=assets,

        weights=weights,

        capital=capital,

        dividends=dividends,

        invested=invested,

        annual_return=0.0

    )

    # -----------------------------------------------------
    # COMPLETE ANALYTICS
    # -----------------------------------------------------
    summary = portfolio_summary(

        portfolio=portfolio,

        invested=invested,

        value=portfolio_value,

        dividends=total_dividends,

        years=years,

        returns=monthly_returns,

        history=curve

    )
    # =====================================================
    # RISK ANALYTICS
    # =====================================================

    risk = portfolio_risk_report(

        returns=monthly_returns.tolist(),

        values=curve

    )

    # -----------------------------------------------------
    # UPDATE PORTFOLIO WITH TRUE CAGR
    # -----------------------------------------------------
    annual_return = summary["cagr"] / 100.0

    for company in portfolio:

        company["annual_return"] = round(

            annual_return * 100,

            2

        )
    # =====================================================
    # AI INVESTMENT ADVISOR
    # =====================================================
    ai = investment_advisor(

        portfolio=portfolio,

        summary=summary,

        mode=mode,

        model=model

    )
    # =====================================================
    # RETIREMENT PROJECTION
    # =====================================================

    retirement = retirement_projection(
        monthly=monthly,
        years=years,
        target=invested * 2
    )

    # =====================================================
    # MONTHLY INVESTMENT PLAN
    # =====================================================

    monthly_plan = build_investment_plan(

        assets=assets,

        weights=weights,

        monthly=monthly

    )

    # =====================================================
    # ASSET RETURNS TABLE
    # =====================================================

    returns_table = build_returns_table(

        portfolio=portfolio

    )

    # =====================================================
    # PERFORMANCE CHART
    # =====================================================
    portfolio_chart = chart(curve)

    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {

        "summary": summary,

        "portfolio": portfolio,

        "plan": monthly_plan,

        "returns": returns_table,

        "curve": curve,

        "chart": portfolio_chart,

        "risk": risk,

        "ai": ai,

        "retirement": retirement

    }
