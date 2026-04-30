import numpy as np

# =========================
# SAFE UTIL
# =========================
def safe(x):
    try:
        if x is None:
            return 0.0
        if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
            return 0.0
        return float(x)
    except:
        return 0.0


# =========================
# ASSET CLASSIFICATION
# =========================
def classify(name):
    n = name.lower()

    if "bond" in n or "treasury" in n:
        return "bond"
    if "reit" in n or "property" in n:
        return "reit"
    if "mmf" in n or "money" in n:
        return "mmf"
    if "gold" in n:
        return "gold"
    return "equity"


# =========================
# BASE RETURNS (REALISTIC KENYA RANGE)
# =========================
BASE = {
    "equity": 0.14,
    "bond": 0.11,
    "reit": 0.13,
    "mmf": 0.10,
    "gold": 0.08
}

DIV = {
    "equity": 0.04,
    "bond": 0.08,
    "reit": 0.07,
    "mmf": 0.09,
    "gold": 0.00
}


# =========================
# SINGLE ASSET SIM
# =========================
def simulate_asset(name, price, monthly, years, scenario=1.0):

    months = years * 12
    shares = 0.0
    price = safe(price, 10)

    curve = []

    cls = classify(name)

    growth = BASE[cls] * scenario
    dividend = DIV[cls]

    cash_div = 0.0

    for _ in range(months):

        shares += monthly / price

        # stable growth (NO EXPLODING VALUES)
        price *= (1 + growth / 12 + np.random.normal(0, 0.003))
        price = max(price, 0.1)

        div = shares * price * dividend / 12
        shares += div / price

        value = shares * price
        curve.append(value)

    invested = monthly * months
    final_value = shares * price
    dividends = final_value * dividend

    return {
        "invested": invested,
        "final_value": final_value,
        "dividends": dividends,
        "total_return": final_value + dividends,
        "roi": ((final_value - invested) / invested) * 100,
        "curve": curve
    }


# =========================
# MAIN ENGINE (USED BY FLASK)
# =========================
def simulate_investment(monthly, years, companies):

    scenarios = {
        "normal": [],
        "defensive": [],
        "aggressive": []
    }

    for c in companies:

        name = c.get("name")
        price = safe(c.get("price"))

        scenarios["normal"].append(
            simulate_asset(name, price, monthly, years, 1.0)
        )

        scenarios["defensive"].append(
            simulate_asset(name, price, monthly, years, 0.85)
        )

        scenarios["aggressive"].append(
            simulate_asset(name, price, monthly, years, 1.15)
        )

    return scenarios, {}