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
