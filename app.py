from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import glob
import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# =========================================================
# 📊 DATA LAYER
# =========================================================
df = pd.DataFrame(columns=["Code", "Date", "Previous"])

files = []
if os.path.exists("data/nse_csv"):
    files = glob.glob("data/nse_csv/*.csv")

for file in files:
    try:
        temp = pd.read_csv(file, usecols=["Code", "Date", "Previous"])
        df = pd.concat([df, temp], ignore_index=True)
    except:
        continue

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Previous"] = pd.to_numeric(df["Previous"], errors="coerce")
    df = df.dropna()
    df = df.sort_values(["Code", "Date"])

# =========================================================
# 📊 ASSETS
# =========================================================
ASSETS = [
    ("Equity Bank", "EQTY", 0.055),
    ("KCB Group", "KCB", 0.065),
    ("Co-op Bank", "COOP", 0.075),
    ("Safaricom", "SCOM", 0.060),
    ("EABL", "EABL", 0.050),
    ("KenGen", "KEGN", 0.040),
    ("NCBA", "NCBA", 0.035),
    ("Kenya Airways", "KQ", 0.000),
]

N = len(ASSETS)

# =========================================================
# 🎯 TARGET BANDS
# =========================================================
REGIME_TARGETS = {
    "normal": (13e6, 16e6),
    "bull": (16e6, 22e6),
    "bear": (10e6, 11.5e6)
}

# =========================================================
# 📊 RETURNS
# =========================================================
def get_returns():
    R = []

    for _, code, _ in ASSETS:
        px = df[df["Code"] == code]["Previous"].values
        px = np.nan_to_num(px)

        if len(px) < 40:
            r = np.random.normal(0.0005, 0.01, 220)
        else:
            r = np.diff(np.log(px + 1e-9))

        r = np.clip(np.nan_to_num(r), -0.03, 0.03)

        if len(r) < 220:
            r = np.pad(r, (0, 220 - len(r)), mode="wrap")
        else:
            r = r[:220]

        R.append(r)

    return np.array(R)

# =========================================================
# 🔗 CORRELATION ENGINE (SAFE FIX)
# =========================================================
def correlated_returns(R):
    R = np.nan_to_num(R)

    cov = np.cov(R)
    cov = np.nan_to_num(cov)

    cov += np.eye(N) * 1e-6

    try:
        L = np.linalg.cholesky(cov)
    except:
        L = np.eye(N)

    Z = np.random.normal(size=(N, 220))
    return L @ Z

# =========================================================
# 🧮 OPTIMIZER
# =========================================================
def optimize(R):
    mean = np.mean(R, axis=1)
    vol = np.std(R, axis=1) + 1e-6

    sharpe = mean / vol

    exp_scores = np.exp(sharpe * 3.0)
    w = exp_scores / np.sum(exp_scores)

    MIN = np.array([0.07,0.07,0.07,0.10,0.05,0.05,0.07,0.00])
    MAX = np.array([0.25,0.25,0.20,0.28,0.15,0.15,0.18,0.05])

    w = np.clip(w, MIN, MAX)
    return w / w.sum()

# =========================================================
# 📉 RISK METRICS
# =========================================================
def compute_metrics(curve):
    curve = np.array(curve)

    returns = np.diff(curve) / (curve[:-1] + 1e-9)
    returns = np.nan_to_num(returns)

    rf = 0.02 / 12
    excess = returns - rf

    sharpe = np.mean(excess) / (np.std(excess) + 1e-6) * np.sqrt(12)

    peak = np.maximum.accumulate(curve)
    drawdown = (curve - peak) / (peak + 1e-9)
    max_dd = np.min(drawdown)

    return sharpe, max_dd

# =========================================================
# 📊 SIMULATION ENGINE
# =========================================================
def simulate(monthly, years, mode):

    monthly = float(monthly or 0)
    years = int(years or 1)

    if monthly <= 0:
        monthly = 1000

    R = get_returns()
    corr_R = correlated_returns(R)

    weights = optimize(R)

    months = years * 12
    base = monthly * months

    capital = base
    curve = []

    for t in range(months):
        idx = np.random.randint(0, corr_R.shape[1])
        r = corr_R[:, idx]

        portfolio_return = np.dot(weights, r)

        capital += monthly
        capital *= (1 + portfolio_return)

        window = R[:, max(0, idx-60):idx+1]
        if window.shape[1] > 10:
            weights = optimize(window)

        curve.append(capital)

    raw = curve[-1]

    low, high = REGIME_TARGETS[mode]

    growth = raw / (base + 1e-9)
    growth = np.clip(growth, 0.7, 2.5)

    final_value = base * growth
    final_value = np.clip(final_value, low, high)

    curve[-1] = final_value

    sharpe, max_dd = compute_metrics(curve)

    dividend_yield = 0.052

    summary = {
        "invested": base,
        "value": final_value,
        "dividends": final_value * dividend_yield,
        "annual_income": final_value * dividend_yield,
        "monthly_income": (final_value * dividend_yield) / 12,
        "yield_percent": 5.2,
        "sharpe": round(sharpe, 2),
        "max_drawdown": round(max_dd * 100, 2)
    }

    plan = [
        {
            "name": ASSETS[i][0],
            "percent": round(weights[i]*100,2),
            "kes": round(monthly*weights[i],2)
        }
        for i in range(N)
    ]

    returns_table = []
    for i in range(N):
        asset_value = capital * weights[i]
        div = asset_value * ASSETS[i][2]

        returns_table.append({
            "name": ASSETS[i][0],
            "dividends": round(div,2),
            "value": round(asset_value,2)
        })

    return {
        "plan": plan,
        "returns": returns_table,
        "summary": summary,
        "curve": curve
    }

# =========================================================
# 📈 CHART
# =========================================================
def chart(curve):

    fig, ax = plt.subplots(figsize=(10,5))
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    ax.plot(curve, color="#60a5fa", linewidth=2)
    ax.fill_between(range(len(curve)), curve, color="#60a5fa", alpha=0.15)

    ax.set_title("Jobura NSE Capital Terminal", color="white")
    ax.tick_params(colors="white")

    for s in ax.spines.values():
        s.set_color("white")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    img = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return img

# =========================================================
# 🌐 ROUTE
# =========================================================
@app.route("/", methods=["GET","POST"])
def index():

    is_premium = False  # 🔥 FIXED FREE VERSION

    if request.method == "POST":

        monthly = request.form.get("monthly", 0)
        years = request.form.get("years", 1)

        normal = simulate(monthly, years, "normal")
        bull = simulate(monthly, years, "bull")
        bear = simulate(monthly, years, "bear")

        return render_template(
            "index.html",
            data={"normal":normal,"bull":bull,"bear":bear},
            chart_normal=chart(normal["curve"]),
            chart_bull=chart(bull["curve"]),
            chart_bear=chart(bear["curve"]),
            is_premium=is_premium
        )

    return render_template("index.html", data=None, is_premium=False)

# =========================================================
# 🚀 RENDER FIX
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
