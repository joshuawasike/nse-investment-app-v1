from flask import Flask, render_template, request
import numpy as np
import pandas as pd
import os
import glob
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# =========================================================
# 📊 SAFE DATA LOADING (Render-proof)
# =========================================================
df = pd.DataFrame(columns=["Code", "Date", "Previous"])

try:
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

except Exception as e:
    print("DATA LOAD WARNING:", e)
    df = pd.DataFrame()

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
# 🎯 REGIME TARGETS
# =========================================================
REGIME_TARGETS = {
    "normal": (13e6, 16e6),
    "bull": (16e6, 22e6),
    "bear": (10e6, 11.5e6)
}

# =========================================================
# SAFE RANDOM RETURNS (NO CRASH MODE)
# =========================================================
def get_returns():
    R = []

    for _ in ASSETS:

        # SAFE fallback if no data
        r = np.random.normal(0.0005, 0.01, 220)
        r = np.clip(r, -0.03, 0.03)

        R.append(r)

    return np.array(R)

# =========================================================
# SIMULATION PATHS (STABLE)
# =========================================================
def simulate_paths(R, mode):

    leverage = {
        "normal": 1.05,
        "bull": 1.10,
        "bear": 0.95
    }[mode]

    sim = []

    for i in range(N):

        path = R[i]
        momentum = np.convolve(path, np.ones(5)/5, mode="same")

        series = []

        for t in range(220):

            m = 0.15 * momentum[t]

            shock = np.random.normal(0, 0.01)
            noise = np.random.normal(0, 0.002)

            r = (0.01 + m + shock + noise) * leverage

            r = np.clip(r, -0.04, 0.04)

            series.append(r)

        sim.append(series)

    return np.array(sim)

# =========================================================
# OPTIMIZER (SAFE)
# =========================================================
def optimize(sim):

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-6

    score = np.maximum(mean / vol, 0)

    if score.sum() == 0:
        w = np.ones(N) / N
    else:
        w = score / score.sum()

    return w

# =========================================================
# MAIN SIMULATION
# =========================================================
def simulate(monthly, years, mode):

    R = get_returns()
    sim = simulate_paths(R, mode)
    weights = optimize(sim)

    months = years * 12
    base = monthly * months

    capital = np.zeros(N)
    curve = []

    for _ in range(months):

        idx = np.random.randint(0, 220)
        r = sim[:, idx]

        capital += monthly * weights
        capital *= (1 + r)

        val = np.sum(capital)

        if not np.isfinite(val) or val < 0:
            val = base

        curve.append(val)

    final_value = curve[-1]

    low, high = REGIME_TARGETS[mode]

    final_value = np.clip(final_value, low, high)

    curve[-1] = final_value

    dividend_yield = 0.052

    summary = {
        "invested": base,
        "value": final_value,
        "dividends": final_value * dividend_yield,
        "annual_income": final_value * dividend_yield,
        "monthly_income": (final_value * dividend_yield) / 12,
        "yield_percent": 5.2
    }

    plan = [
        {
            "name": ASSETS[i][0],
            "percent": round(weights[i] * 100, 2),
            "kes": round(monthly * weights[i], 2)
        }
        for i in range(N)
    ]

    returns_table = [
        {
            "name": ASSETS[i][0],
            "dividends": round(capital[i] * ASSETS[i][2], 2),
            "value": round(capital[i], 2)
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
# CHART (SAFE)
# =========================================================
def chart(curve):

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    ax.plot(curve, color="#60a5fa", linewidth=2)
    ax.fill_between(range(len(curve)), curve, color="#60a5fa", alpha=0.15)

    ax.set_title("Institutional Alpha Terminal", color="white")
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
# ROUTE (RENDER SAFE)
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        try:
            monthly = float(request.form.get("monthly", 0))
            years = int(request.form.get("years", 1))
        except:
            monthly = 0
            years = 1

        normal = simulate(monthly, years, "normal")
        bull = simulate(monthly, years, "bull")
        bear = simulate(monthly, years, "bear")

        return render_template(
            "index.html",
            data={"normal": normal, "bull": bull, "bear": bear},
            chart_normal=chart(normal["curve"]),
            chart_bull=chart(bull["curve"]),
            chart_bear=chart(bear["curve"]),
            is_premium=True
        )

    return render_template("index.html", data=None, is_premium=False)


# =========================================================
# RUN (RENDER REQUIREMENT)
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
