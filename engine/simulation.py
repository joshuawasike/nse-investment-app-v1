"""
=========================================================
JOBURA WEALTH®
Simulation Engine
Version 1.0
=========================================================
"""
import numpy as np
import random

REGIMES={
    "normal":{"mu":0.10,"vol":0.18},
    "bull":{"mu":0.22,"vol":0.24},
    "bear":{"mu":-0.08,"vol":0.30},
}

def simulate_market(initial_value=1000000,years=5,mode="normal",seed=None):
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    cfg=REGIMES.get(mode,REGIMES["normal"])
    months=years*12
    monthly_mu=cfg["mu"]/12
    monthly_sigma=cfg["vol"]/np.sqrt(12)
    values=[float(initial_value)]
    monthly_returns=[]
    for _ in range(months):
        shock=np.random.standard_t(df=6)*monthly_sigma
        r=monthly_mu+shock
        monthly_returns.append(float(r))
        values.append(values[-1]*(1+r))
    return {
        "mode":mode,
        "years":years,
        "initial_value":initial_value,
        "final_value":round(values[-1],2),
        "history":[round(v,2) for v in values],
        "returns":monthly_returns
    }

def monte_carlo(initial_value=1000000,years=5,mode="normal",simulations=500):
    finals=[]
    for i in range(simulations):
        s=simulate_market(initial_value,years,mode)
        finals.append(s["final_value"])
    return {
        "simulations":simulations,
        "mean":round(float(np.mean(finals)),2),
        "median":round(float(np.median(finals)),2),
        "best":round(float(np.max(finals)),2),
        "worst":round(float(np.min(finals)),2),
        "p5":round(float(np.percentile(finals,5)),2),
        "p95":round(float(np.percentile(finals,95)),2),
    }
# =========================================================
# 🌍 INSTITUTIONAL ECONOMIC REGIME ENGINE V2
# =========================================================

ECONOMIC_REGIMES = {

    # -----------------------------------------------------
    # NORMAL ECONOMY
    # -----------------------------------------------------
    "normal": {

        # Multiplier applied to historical expected returns
        "drift": 1.00,

        # Absolute monthly return adjustment
        "alpha": 0.0000,

        # Volatility multiplier
        "vol": 1.00,

        # Dividend adjustment
        "dividend": 1.00,

        # Corporate earnings adjustment
        "earnings": 1.00,

        # Sector performance
        "sector": {

            "Banking":   1.00,
            "Telecom":   1.00,
            "Consumer":  1.00,
            "Utilities": 1.00,
            "Airline":   1.00

        }

    },

    # -----------------------------------------------------
    # BULL MARKET
    # -----------------------------------------------------
    "bull": {

        # Historical returns increase slightly
        "drift": 1.10,

        # Extra monthly return boost
        "alpha": 0.0020,

        # Lower volatility
        "vol": 0.80,

        # Higher dividend growth
        "dividend": 1.12,

        # Higher earnings
        "earnings": 1.15,

        "sector": {

            "Banking":   1.20,
            "Telecom":   1.12,
            "Consumer":  1.15,
            "Utilities": 1.00,
            "Airline":   1.50

        }

    },

    # -----------------------------------------------------
    # BEAR MARKET
    # -----------------------------------------------------
    "bear": {

        # Slight reduction in historical returns
        "drift": 0.90,

        # Negative monthly return adjustment
        "alpha": -0.0020,

        # Higher volatility
        "vol": 1.55,

        # Dividend cuts
        "dividend": 0.82,

        # Earnings contraction
        "earnings": 0.85,

        "sector": {

            "Banking":   0.75,
            "Telecom":   0.95,
            "Consumer":  0.82,
            "Utilities": 1.05,
            "Airline":   0.30

        }

    }

}
# =========================================================
# 🌍 INSTITUTIONAL MARKET GENERATOR V13
# Historical NSE Monte Carlo Engine
# =========================================================
def generate_market(mode, N, drift, vol, momentum):

    stats = get_market_stats()

    periods = 300

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------
    if stats is None:

        return np.random.normal(
            drift,
            vol,
            (N, periods)
        )

    # -----------------------------------------------------
    # HISTORICAL PARAMETERS
    # -----------------------------------------------------
    mu = stats["mu"].copy()
    sigma = stats["sigma"].copy()
    cov = stats["cov"].copy()

    # -----------------------------------------------------
    # MATCH NSE UNIVERSE
    # -----------------------------------------------------
    codes = [asset[1] for asset in ASSETS]

    available = [
        c for c in codes
        if (
            c in mu.index and
            c in sigma.index and
            c in cov.index
        )
    ]

    if len(available) < 2:

        return np.random.normal(
            drift,
            vol,
            (N, periods)
        )

    mu = mu.loc[available]
    sigma = sigma.loc[available]
    cov = cov.loc[available, available]

    # -----------------------------------------------------
    # ECONOMIC REGIME
    # -----------------------------------------------------
    regime = ECONOMIC_REGIMES.get(
        mode,
        ECONOMIC_REGIMES["normal"]
    )

    # -----------------------------------------------------
    # SECTOR ADJUSTMENTS
    # -----------------------------------------------------
    sector_multiplier = []

    for code in available:

        profile = DIVIDEND_DATABASE.get(code, {})

        sector = profile.get(
            "sector",
            "Banking"
        )

        sector_multiplier.append(

            regime["sector"].get(
                sector,
                1.0
            )

        )

    sector_multiplier = np.array(sector_multiplier)

    # -----------------------------------------------------
    # EXPECTED RETURNS
    # -----------------------------------------------------
    mu = (
        mu
        * sector_multiplier
        * regime["drift"]
    ) + regime["alpha"]

    mu = np.clip(
        mu,
        -0.015,
        0.015
    )

    # -----------------------------------------------------
    # VOLATILITY
    # -----------------------------------------------------
    sigma *= np.sqrt(regime["vol"])

    cov *= regime["vol"]

    # -----------------------------------------------------
    # POSITIVE DEFINITE COVARIANCE
    # -----------------------------------------------------
    cov += np.eye(len(cov)) * 1e-8

    try:

        L = np.linalg.cholesky(cov)

    except np.linalg.LinAlgError:

        eigvals, eigvecs = np.linalg.eigh(cov)

        eigvals[eigvals < 1e-8] = 1e-8

        cov = eigvecs @ np.diag(eigvals) @ eigvecs.T

        L = np.linalg.cholesky(cov)

    # -----------------------------------------------------
    # FAT-TAIL MONTE CARLO
    # -----------------------------------------------------
    shocks = np.random.standard_t(
        df=6,
        size=(len(mu), periods)
    )

    correlated = L @ shocks

    # -----------------------------------------------------
    # MOMENTUM PROCESS
    # -----------------------------------------------------
    phi = np.clip(momentum, 0.15, 0.95)

    trend = np.zeros_like(correlated)

    for t in range(1, periods):

        trend[:, t] = (

            phi * trend[:, t-1]

            + correlated[:, t]

        )

    # -----------------------------------------------------
    # FINAL RETURNS
    # -----------------------------------------------------
    R = mu.values[:, None] + trend

    # -----------------------------------------------------
    # MATCH HISTORICAL VOLATILITY
    # -----------------------------------------------------
    current_std = np.std(
        R,
        axis=1,
        keepdims=True
    )

    current_std[current_std == 0] = 1e-8

    target_std = sigma.values[:, None]

    R *= target_std / current_std

    # -----------------------------------------------------
    # EXTREME EVENT SIMULATION
    # -----------------------------------------------------
    shock_probability = 0.015

    disaster = np.random.rand(
        len(mu),
        periods
    ) < shock_probability

    if mode == "bull":

        disaster_returns = np.random.uniform(
            -0.04,
            -0.02,
            disaster.shape
        )

    elif mode == "bear":

        disaster_returns = np.random.uniform(
            -0.12,
            -0.05,
            disaster.shape
        )

    else:

        disaster_returns = np.random.uniform(
            -0.08,
            -0.03,
            disaster.shape
        )

    R[disaster] += disaster_returns[disaster]

    # -----------------------------------------------------
    # SAFETY LIMITS
    # -----------------------------------------------------
    R = np.clip(
        R,
        -0.15,
        0.18
    )

    # -----------------------------------------------------
    # PAD IF NECESSARY
    # -----------------------------------------------------
    if len(mu) < N:

        extra = np.random.normal(

            drift,

            vol,

            (N-len(mu), periods)

        )

        R = np.vstack([R, extra])

    return R[:N]
    # =========================================================
# 🧠 PATH SIMULATION (MISSING FUNCTION FIX)
# =========================================================
def simulate_paths(R, mode):

    REGIME = {
        "normal": {"mu": 0.0025, "vol": 1.0},
        "bull":   {"mu": 0.0055, "vol": 1.2},
        "bear":   {"mu": -0.0035, "vol": 1.3},
    }

    cfg = REGIME.get(mode, REGIME["normal"])
    N = R.shape[0]
    T = R.shape[1]

    sim = []

    for i in range(N):
        base_vol = np.std(R[i]) + 1e-9
        series = []

        for t in range(T):
            shock = np.random.standard_t(5) * base_vol * cfg["vol"]
            step = R[i][t] + cfg["mu"] + shock

            if mode == "bear":
                step = np.clip(step, -0.05, 0.01)

            series.append(step)

        sim.append(series)

    return np.array(sim)
# =========================================================
# 📈 FULL INSTITUTIONAL SIMULATION ENGINE V11
# =========================================================
def simulate(monthly, years, mode, model="dividend"):

    # -----------------------------------------------------
    # MODEL CONFIGURATION
    # -----------------------------------------------------
    MODEL_PARAMS = {
        "dividend": (0.0035, 0.012, 0.60),
        "growth":   (0.0060, 0.022, 1.10),
        "banking":  (0.0045, 0.016, 0.80),
        "value":    (0.0040, 0.015, 0.75),
        "income":   (0.0038, 0.013, 0.70),
    }

    drift, vol, momentum = MODEL_PARAMS.get(
        model,
        MODEL_PARAMS["dividend"]
    )

    # -----------------------------------------------------
    # MARKET
    # -----------------------------------------------------
    R_full = generate_market(
        mode,
        len(ASSETS),
        drift,
        vol,
        momentum
    )

    # -----------------------------------------------------
    # SELECT MODEL ASSETS
    # -----------------------------------------------------
    assets = get_model_assets(model)

    names = [a[0] for a in ASSETS]
    selected = [a[0] for a in assets]

    idx = [
        names.index(n)
        for n in selected
        if n in names
    ]

    if len(idx) == 0:
        idx = list(range(len(ASSETS)))
        assets = ASSETS

    R = R_full[idx]
 # -----------------------------------------------------
    # SIMULATION SETTINGS
    # -----------------------------------------------------
    months = years * 12

    invested = monthly * months

    nav = 0.0

    curve = []

    dividends = np.zeros(len(weights))

    yield_table = estimate_dividend_yields(mode, model)
    stats = get_market_stats()

    yields = np.array([

        yield_table.get(asset[1],0.05)

        for asset in assets

    ])
    capital = np.zeros(len(weights))

    # -----------------------------------------------------
    # REGIME DIVIDEND MULTIPLIER
    # -----------------------------------------------------
    regime_multiplier = {
        "normal": 1.00,
        "bull": 1.15,
        "bear": 0.85
    }.get(mode, 1.0)

    # -----------------------------------------------------
    # MONTHLY LOOP
    # -----------------------------------------------------
    for m in range(months):

        col = m % R.shape[1]

        # yearly rebalance
        if m > 0 and m % 12 == 0:

            weights = institutional_allocator(R, mode)
            weights = apply_model_bias(weights, model)

            if len(weights) > len(assets):
                weights = weights[:len(assets)]

            weights = weights / np.sum(weights)

        portfolio_return = np.dot(weights, R[:, col])

        if mode == "bull":
            portfolio_return = np.clip(portfolio_return, -0.03, 0.08)

        elif mode == "bear":
            portfolio_return = np.clip(portfolio_return, -0.05, 0.03)

        else:
            portfolio_return = np.clip(portfolio_return, -0.04, 0.05)

        nav *= (1 + portfolio_return)

        nav += monthly

        curve.append(nav)

        # Monthly contribution
        monthly_alloc = monthly * weights

        # Add new investment
        capital += monthly_alloc

        # Grow each asset using its own return
        asset_returns = R[:, col]

        capital *= (1 + asset_returns)
        current_month = (m % 12) + 1


        # -----------------------------------------------------
        # DIVIDEND PAYMENT ENGINE
        # -----------------------------------------------------
        current_month = (m % 12) + 1

        for i, asset in enumerate(assets):

            code = asset[1]

            profile = DIVIDEND_DATABASE.get(code, {})

            payment_months = profile.get("months", [])

            growth = profile.get("growth", 0.00)

            stability = profile.get("stability", 0.90)

            payout = profile.get("payout", 0.40)

            years_elapsed = m / 12

            dividend_yield = forecast_dividend_yield(
                code,
                years_elapsed,
                mode
            )

            current_month = (m % 12) + 1

            if current_month in payment_months:

                payments = len(payment_months)

                dividend = (
                    capital[i]
                    * dividend_yield
                    * payout
                    * regime_multiplier
                    / payments
                )

                capital[i], bonus = apply_corporate_actions(
                    capital[i],
                    code
                )
    
                dividends[i] += dividend + bonus
    # -----------------------------------------------------
    # FINAL VALUES
    # -----------------------------------------------------
    final_nav = curve[-1]

    total_dividends = float(dividends.sum())

    portfolio_value = float(final_nav + total_dividends)

    curve_np = np.array(curve)

    monthly_returns = np.diff(curve_np) / np.maximum(curve_np[:-1], 1)

    annual_return = (portfolio_value / invested) ** (1 / years) - 1

    cagr = annual_return

    volatility = np.std(monthly_returns) * np.sqrt(12)

    sharpe = (
        annual_return - 0.05
    ) / max(volatility, 1e-9)

    running_max = np.maximum.accumulate(curve_np)

    drawdown = (curve_np - running_max) / running_max

    max_drawdown = abs(np.min(drawdown))

    inflation = 0.05

    real_value = portfolio_value / ((1 + inflation) ** years)

     # -----------------------------------------------------
    # AI
    # -----------------------------------------------------
    ai = ai_portfolio_advisor(
        weights,
        R,
        assets
    )
summary = {

    "invested": round(float(invested), 2),

    "value": round(float(portfolio_value), 2),

    "real_value": round(float(real_value), 2),

    "dividends": round(total_dividends, 2),

    "annual_return": round(annual_return * 100, 2),

    "cagr": round(cagr * 100, 2),

    "volatility": round(volatility * 100, 2),

    "sharpe": round(sharpe, 2),

    "max_drawdown": round(max_drawdown * 100, 2)

}

return {

    "summary": summary,

    "curve": curve,

    "plan": plan,

    "ai": ai,

    "assets": breakdown,

    "returns": returns_table

}
