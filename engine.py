import numpy as np

# =========================
# SAFE UTIL
# =========================
def safe(x, default=0.0):
    try:
        if x is None:
            return default
        x = float(x)
        if np.isnan(x) or np.isinf(x):
            return default
        return x
    except:
        return default


# =========================
# CLASSIFICATION
# =========================
def classify(name):
    n = str(name).lower()

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
# BASE RETURNS
# =========================
BASE = {
    "equity": 0.12,
    "bond": 0.10,
    "reit": 0.11,
    "mmf": 0.09,
    "gold": 0.07
}

DIV = {
    "equity": 0.04,
    "bond": 0.07,
    "reit": 0.06,
    "mmf": 0.08,
    "gold": 0.00
}


# =========================
# SINGLE ASSET SIMULATION
# =========================
def simulate_asset(name, price, monthly, years, scenario=1.0):

    price = safe(price, 10)
    monthly = safe(monthly, 0)
    years = max(int(safe(years, 1)), 1)

    cls = classify(name)

    growth = BASE[cls] * scenario
    dividend_yield = DIV[cls]

    shares = 0.0
    curve = []

    months = years * 12

    for _ in range(months):

        if price <= 0:
            price = 10

        # DCA (safe division)
        shares += monthly / (price + 1e-9)

        # controlled stochastic growth
        shock = np.random.normal(0, 0.002)
        price *= (1 + (growth / 12) + shock)

        price = max(price, 0.1)

        # dividends reinvested
        div = shares * price * dividend_yield / 12
        shares += div / (price + 1e-9)

        value = shares * price

        if not np.isfinite(value):
            value = monthly * months

        curve.append(value)

    invested = monthly * months
    final_value = curve[-1] if len(curve) > 0 else invested

    dividends = final_value * dividend_yield

    roi = 0.0
    if invested > 0:
        roi = ((final_value - invested) / invested) * 100

    # safety clamp
    final_value = safe(final_value, invested)
    dividends = safe(dividends, 0)
    roi = safe(roi, 0)

    return {
        "invested": invested,
        "final_value": final_value,
        "dividends": dividends,
        "total_return": final_value + dividends,
        "roi": roi,
        "curve": curve
    }


# =========================
# MAIN ENGINE
# =========================
def simulate_investment(monthly, years, companies):

    monthly = safe(monthly, 0)
    years = max(int(safe(years, 1)), 1)

    companies = companies or []

    scenarios = {
        "normal": [],
        "defensive": [],
        "aggressive": []
    }

    # guard: empty input
    if len(companies) == 0:
        return scenarios, {"status": "no data"}

    for c in companies:

        # safety: must be dict
        if not isinstance(c, dict):
            continue

        name = c.get("name", "asset")
        price = safe(c.get("price", 10))

        scenarios["normal"].append(
            simulate_asset(name, price, monthly, years, 1.0)
        )

        scenarios["defensive"].append(
            simulate_asset(name, price, monthly, years, 0.85)
        )

        scenarios["aggressive"].append(
            simulate_asset(name, price, monthly, years, 1.15)
        )

    return scenarios, {
        "status": "ok",
        "assets": len(companies)
    }
