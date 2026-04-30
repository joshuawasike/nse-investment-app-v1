from flask import Flask, render_template, request
import pandas as pd
import glob
import random

app = Flask(__name__)

# =========================
# 📊 LOAD & CLEAN NSE DATA
# =========================
files = glob.glob("data/nse_csv/*.csv")

df_list = []
for file in files:
    temp = pd.read_csv(file)
    df_list.append(temp)

df = pd.concat(df_list, ignore_index=True)

df.columns = df.columns.str.strip()

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Previous"] = pd.to_numeric(df["Previous"], errors="coerce")

df = df.dropna(subset=["Date", "Previous"])
df = df.sort_values("Date")

print("✅ NSE data loaded:", len(df), "rows")


# =========================
# 📈 REAL RETURN FUNCTION
# =========================
def get_stock_return(code):

    stock = df[df["Code"] == code]

    if len(stock) < 50:
        return 0.10  # fallback

    start_price = stock.iloc[0]["Previous"]
    end_price = stock.iloc[-1]["Previous"]

    years = (stock.iloc[-1]["Date"] - stock.iloc[0]["Date"]).days / 365

    if years <= 0:
        return 0.10

    return (end_price / start_price) ** (1 / years) - 1


# =========================
# 📊 COMPANY MODEL (WITH DIVIDENDS)
# =========================
BASE_COMPANIES = [
    {"name": "Equity Bank", "code": "EQTY", "weight": 0.15, "dividend": 0.05},
    {"name": "KCB Group", "code": "KCB", "weight": 0.15, "dividend": 0.06},
    {"name": "Co-op Bank", "code": "COOP", "weight": 0.10, "dividend": 0.07},
    {"name": "Safaricom", "code": "SCOM", "weight": 0.25, "dividend": 0.06},
    {"name": "EABL", "code": "EABL", "weight": 0.10, "dividend": 0.05},
    {"name": "KenGen", "code": "KEGN", "weight": 0.10, "dividend": 0.04},
    {"name": "NCBA", "code": "NCBA", "weight": 0.10, "dividend": 0.03},
    {"name": "Kenya Airways", "code": "KQ", "weight": 0.05, "dividend": 0.00},
]


# =========================
# 👤 INVESTOR PROFILES
# =========================
def get_companies(profile):

    if profile == "conservative":
        return [
            {"name": "Co-op Bank", "code": "COOP", "weight": 0.35, "dividend": 0.08},
            {"name": "Safaricom", "code": "SCOM", "weight": 0.40, "dividend": 0.07},
            {"name": "KenGen", "code": "KEGN", "weight": 0.25, "dividend": 0.05},
        ]

    elif profile == "aggressive":
        return [
            {"name": "Equity Bank", "code": "EQTY", "weight": 0.25, "dividend": 0.04},
            {"name": "NCBA", "code": "NCBA", "weight": 0.20, "dividend": 0.03},
            {"name": "EABL", "code": "EABL", "weight": 0.20, "dividend": 0.04},
            {"name": "Kenya Airways", "code": "KQ", "weight": 0.15, "dividend": 0.00},
            {"name": "Safaricom", "code": "SCOM", "weight": 0.20, "dividend": 0.05},
        ]

    return BASE_COMPANIES


# =========================
# 💰 ENGINE (REALISTIC DIVIDENDS)
# =========================
def simulate(monthly, years, companies, boost=1.0):

    months = years * 12
    portfolio = 0
    curve = []

    plan = []
    returns = []

    total_dividends = 0

    # normalize weights
    total_weight = sum(c["weight"] for c in companies)
    for c in companies:
        c["weight"] /= total_weight

    # monthly plan
    for c in companies:
        allocation = monthly * c["weight"]

        plan.append({
            "name": c["name"],
            "percent": int(c["weight"] * 100),
            "kes": round(allocation, 2)
        })

    # simulation loop
    for m in range(months):

        portfolio += monthly
        monthly_return = 0

        for c in companies:
            real_growth = get_stock_return(c["code"])
            div_yield = c.get("dividend", 0)

            r = (real_growth * boost) + div_yield
            monthly_r = (1 + r) ** (1/12) - 1

            monthly_return += monthly_r * c["weight"]

        # ✅ PAY DIVIDENDS YEARLY
        if m % 12 == 0 and m != 0:
            for c in companies:
                div_yield = c.get("dividend", 0)
                annual_div = (portfolio * div_yield) * c["weight"]
                total_dividends += annual_div

        # randomness
        shock = random.uniform(-0.04, 0.04)
        monthly_return += shock / 12

        portfolio *= (1 + monthly_return)
        curve.append(round(portfolio, 2))

    # returns per asset
    for c in companies:
        returns.append({
            "name": c["name"],
            "dividends": round(total_dividends * c["weight"], 2),
            "value": round(portfolio * c["weight"], 2)
        })

    summary = {
        "invested": monthly * months,
        "dividends": round(total_dividends, 2),
        "value": round(portfolio, 2)
    }

    return {
        "plan": plan,
        "returns": returns,
        "summary": summary,
        "curve": curve
    }


# =========================
# 🌐 ROUTE
# =========================
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        try:
            monthly = float(request.form.get("monthly", 0))
            years = int(request.form.get("years", 1))
            profile = request.form.get("profile", "balanced")

            companies = get_companies(profile)

            data = {
                "bull": simulate(monthly, years, companies, boost=1.2),
                "normal": simulate(monthly, years, companies, boost=1.0),
                "bear": simulate(monthly, years, companies, boost=0.7),
            }

            return render_template("index.html", data=data, years=years)

        except Exception as e:
            return f"ERROR: {str(e)}"

    return render_template("index.html", data=None)


# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)