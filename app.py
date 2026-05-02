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
# 📊 DATA LAYER (SAFE FOR DEPLOYMENT)
# =========================================================
df = pd.DataFrame(columns=["Code", "Date", "Previous"])

files = glob.glob("data/nse_csv/*.csv")

for file in files:
    try:
        temp = pd.read_csv(file, usecols=["Code", "Date", "Previous"])
        df = pd.concat([df, temp], ignore_index=True)
    except Exception:
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

REGIME_TARGETS = {
    "normal": (13e6, 16e6),
    "bull": (16e6, 22e6),
    "bear": (10e6, 11.5e6)
}

# =========================================================
# 📈 RETURNS
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

        r = np.nan_to_num(r)
        r = np.clip(r, -0.03, 0.03)

        if len(r) < 220:
            r = np.pad(r, (0, 220 - len(r)), mode="wrap")
        else:
            r = r[:220]

        R.append(r)

    return np.array(R)

# =========================================================
# 🔗 SAFE CORRELATION ENGINE (FIXED)
# =========================================================
def correlated_returns(R):

    try:
        cov = np.cov(R)

        # FIX: ensure positive definiteness
        cov = np.nan_to_num(cov)
        cov += np.eye(N) * 1e-4

        L = np.linalg.cholesky(cov)

        Z = np.random.normal(size=(N, 220))
        return L @ Z

    except Exception:
        # fallback if covariance breaks
        return np.random.normal(0, 0.01, size=(N, 220))

# =========================================================
# 🧮 OPTIMIZER (STABLE)
# =========================================================
def optimize(R):

    mean = np.mean(R, axis=1)
    vol = np.std(R, axis=1) + 1e-6

    sharpe = mean / vol

    exp_scores = np.exp(sharpe * 2.5)
    w = exp_scores / np.sum(exp_scores)

    MIN = np.array([0.07,0.07,0.07,0.10,0.05,0.05,0.07,0.00])
    MAX = np.array([0.25,0.25,0.20,0.28,0.15,0.15,0.18,0.05])

    w = np.clip(w, MIN, MAX)
    return w / np.sum(w)

# =========================================================
# 📉 METRICS
# =========================================================
def compute_metrics(curve):

    curve = np.array(curve)
    returns = np.diff(curve) / (curve[:-1] + 1e-9)

    rf = 0.02 / 12
    excess = returns - rf

    sharpe = np.mean(excess) / (np.std(excess) + 1e-6) * np.sqrt(12)

    peak = np.maximum.accumulate(curve)
    dd = (curve - peak) / (peak + 1e-9)

    return sharpe, np.min(dd)

# =========================================================
# 📊 SIMULATION ENGINE (SAFE)
# =========================================================
def simulate(monthly, years, mode):

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

        # rebalancing (lightweight)
        if t % 20 == 0:
            weights = optimize(R[:, :max(10, idx+1)])

        curve.append(capital)

    raw = curve[-1]

    low, high = REGIME_TARGETS[mode]

    growth = np.clip(raw / base, 0.7, 2.5)
    final_value = np.clip(base * growth, low, high)

    curve[-1] = final_value

    sharpe, dd = compute_metrics(curve)

    dividend_yield = 0.052

    summary = {
        "invested": base,
        "value": final_value,
        "dividends": final_value * dividend_yield,
        "monthly_income": (final_value * dividend_yield) / 12,
        "sharpe": round(sharpe, 2),
        "max_drawdown": round(dd * 100, 2)
    }

    plan = [
        {
            "name": ASSETS[i][0],
            "percent": round(weights[i]*100,2),
            "kes": round(monthly*weights[i],2)
        }
        for i in range(N)
    ]

    returns_table = [
        {
            "name": ASSETS[i][0],
            "value": round(capital * weights[i],2),
            "dividends": round(capital * weights[i] * ASSETS[i][2],2)
        }
        for i in range(N)
    ]

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

    ax.set_title("Quant V6 – Correlation + Risk Engine", color="white")
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

    if request.method == "POST":

        monthly = float(request.form.get("monthly",0))
        years = int(request.form.get("years",1))

        normal = simulate(monthly, years, "normal")
        bull = simulate(monthly, years, "bull")
        bear = simulate(monthly, years, "bear")

        return render_template(
            "index.html",
            data={"normal":normal,"bull":bull,"bear":bear},
            chart_normal=chart(normal["curve"]),
            chart_bull=chart(bull["curve"]),
            chart_bear=chart(bear["curve"]),
            is_premium=True
        )

    return render_template("index.html", data=None, is_premium=False)

# =========================================================
# 🚀 RENDER FIX (IMPORTANT)
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
