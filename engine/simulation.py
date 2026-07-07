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
