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
