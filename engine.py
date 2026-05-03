import numpy as np


# =========================================================
# SAFE CONVERSION
# =========================================================
def safe(x, default=0.0):
    try:
        x = float(x)
        if np.isnan(x) or np.isinf(x):
            return default
        return x
    except:
        return default


# =========================================================
# CLASSIFICATION SYSTEM
# =========================================================
def classify(name):
    n = str(name).lower()

    if "bond" in n:
        return "bond"
    if "reit" in n:
        return "reit"
    if "mmf" in n or "money" in n:
        return "mmf"

    return "equity"


# =========================================================
# CORE RETURN ASSUMPTIONS (kept stable)
# =========================================================
BASE_RETURN = {
    "equity": 0.13,
    "bond": 0.10,
    "reit": 0.12,
    "mmf": 0.09
}

DIV_YIELD = {
    "equity": 0.04,
    "bond": 0.08,
    "reit": 0.06,
    "mmf": 0.09
}


# =========================================================
# PORTFOLIO ENGINE (V9 FIXED CORE)
# =========================================================
def simulate_investment(monthly, years, companies):

    monthly = max(1.0, safe(monthly))
    years = max(1, int(years))

    months = years * 12
    total_invested = monthly * months

    n = len(companies)
    if n == 0:
        return {}, {}

    # equal initial weights (stable baseline)
    weights = np.ones(n) / n

    portfolio_value = 0.0
    curve = []

    seed = int(monthly * 10 + years)
    np.random.seed(seed % 2_147_483_647)

    # =====================================================
    # MONTHLY SIMULATION LOOP
    # =====================================================
    for t in range(months):

        monthly_growth = 0.0

        for i, c in enumerate(companies):

            name = c.get("name", "equity")
            cls = classify(name)

            drift = BASE_RETURN[cls]

            # controlled noise (stability upgrade)
            noise = np.random.normal(0, 0.008)

            asset_return = (drift / 12.0) + noise

            contribution = monthly * weights[i]

            portfolio_value += contribution
            portfolio_value *= (1.0 + asset_return)

            monthly_growth += asset_return * weights[i]

        curve.append(portfolio_value)

        # gentle rebalancing (NOT aggressive flipping)
        if t % 6 == 0:
            weights = np.ones(n) / n

    final_value = float(curve[-1])

    # =====================================================
    # GROWTH NORMALIZATION (soft realism guard)
    # =====================================================
    growth = final_value / (total_invested + 1e-9)

    growth = np.clip(growth, 0.3, 40)

    final_value = total_invested * growth

    # =====================================================
    # SCENARIO OUTPUTS
    # =====================================================
    return {
        "normal": build_result(final_value, total_invested, curve),
        "defensive": build_result(final_value * 0.85, total_invested, curve),
        "aggressive": build_result(final_value * 1.15, total_invested, curve)
    }, {}


# =========================================================
# RESULT BUILDER (CLEAN FINANCIAL LOGIC)
# =========================================================
def build_result(final_value, invested, curve):

    if invested <= 0:
        invested = 1

    dividends = final_value * 0.05

    roi = ((final_value - invested) / invested) * 100

    return {
        "invested": round(invested, 2),
        "final_value": round(final_value, 2),
        "dividends": round(dividends, 2),
        "roi": round(roi, 2),
        "curve": curve
    }
