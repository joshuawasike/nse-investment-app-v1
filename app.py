from flask import Flask, render_template, request, redirect, session
import pandas as pd
import numpy as np
import glob
import matplotlib
import json
import os
from datetime import datetime, timedelta
import io
import base64

matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "jobura_secure_key_change_me"

# =========================================================
# 🔐 ADMIN
# =========================================================
ADMIN_PASSWORD = "Jobura@542542"

# =========================================================
# 📂 USERS DB
# =========================================================
DB_FILE = "users.json"

def load_users():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

# =========================================================
# 📊 LOAD DATA (FIXED - NO SILENT FAILURES)
# =========================================================
df = pd.DataFrame(columns=["Code", "Date", "Previous"])

files = glob.glob("data/nse_csv/*.csv")
print("📂 FILES FOUND:", len(files))

for file in files:
    try:
        temp = pd.read_csv(file, usecols=["Code", "Date", "Previous"])
        df = pd.concat([df, temp], ignore_index=True)
    except Exception as e:
        print("❌ CSV ERROR:", file, e)

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Previous"] = pd.to_numeric(df["Previous"], errors="coerce")
    df = df.dropna()
    df = df.sort_values(["Code", "Date"])

print("📊 DATA SIZE:", len(df))

# =========================================================
# 📊 ASSETS
# =========================================================
ASSETS = [
    ("Equity Bank", "EQTY", 0.085),
    ("KCB Group", "KCB", 0.075),
    ("Co-op Bank", "COOP", 0.080),
    ("Safaricom", "SCOM", 0.065),
    ("EABL", "EABL", 0.060),
    ("KenGen", "KEGN", 0.070),
    ("NCBA", "NCBA", 0.055),
    ("Kenya Airways", "KQ", 0.000),
]

N = len(ASSETS)

# =========================================================
# 📈 RETURNS ENGINE
# =========================================================
def get_returns():
    R = []

    for _, code, _ in ASSETS:
        px = df[df["Code"] == code]["Previous"].values
        px = np.nan_to_num(px)

        if len(px) < 40:
            r = np.full(300, 0.005)
        else:
            r = np.diff(np.log(px + 1e-9))
            r = np.nan_to_num(r)

        r = np.clip(r * 16, -0.05, 0.05)

        if len(r) < 300:
            r = np.pad(r, (0, 300 - len(r)), mode="edge")
        else:
            r = r[:300]

        R.append(r)

    return np.array(R)

# =========================================================
# 🧠 SIMULATION ENGINE
# =========================================================
def simulate_paths(R, mode):

    REGIME = {
        "normal": {"mu": 0.0025, "vol": 1.0},
        "bull":   {"mu": 0.0055, "vol": 1.2},
        "bear":   {"mu": -0.0035, "vol": 1.3},
    }

    cfg = REGIME[mode]
    sim = []

    for i in range(N):
        base_vol = np.std(R[i]) + 1e-9
        series = []

        for t in range(300):
            shock = np.random.standard_t(5) * base_vol * cfg["vol"]
            step = R[i][t] + cfg["mu"] + shock

            if mode == "bear":
                step = np.clip(step, -0.05, 0.01)

            series.append(step)

        sim.append(series)

    return np.array(sim)

# =========================================================
# 🧠 OPTIMIZER
# =========================================================
def optimize(sim):

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9
    downside = np.mean(np.minimum(sim, 0), axis=1)

    score = (mean / vol) - (1.1 * np.abs(downside))
    score[3] *= 1.3
    score[7] *= 0.01

    score = np.tanh(score * 2.0)

    weights = np.exp(score)
    weights = weights / np.sum(weights)

    return weights

# =========================================================
# 💰 DIVIDENDS
# =========================================================
def dividend_engine(asset_investment):
    yields = np.array([a[2] for a in ASSETS])
    return asset_investment * yields

# =========================================================
# 📊 MAIN SIMULATION
# =========================================================
def simulate(monthly, years, mode):

    R = get_returns()
    sim = simulate_paths(R, mode)
    weights = optimize(sim)

    months = years * 12
    invested_total = monthly * months

    nav = invested_total
    curve = []

    for t in range(months):
        idx = t % sim.shape[1]
        port_ret = np.dot(weights, sim[:, idx])

        if mode == "bear":
            port_ret *= 0.6

        nav = nav * (1 + port_ret) + monthly
        curve.append(nav)

    asset_investment = invested_total * weights
    asset_dividends = dividend_engine(asset_investment)

    returns = [
        {
            "name": ASSETS[i][0],
            "dividends": round(asset_dividends[i], 2),
            "value": round(asset_investment[i] * (1 + 0.1 * years), 2)
        }
        for i in range(N)
    ]

    return {
        "summary": {
            "invested": invested_total,
            "value": nav,
            "dividends": float(np.sum(asset_dividends)),
            "monthly_income": float(np.sum(asset_dividends)) / months,
            "annual_income": float(np.sum(asset_dividends)) / years
        },
        "plan": [
            {
                "name": ASSETS[i][0],
                "percent": round(weights[i] * 100, 2),
                "kes": round(monthly * weights[i], 2)
            }
            for i in range(N)
        ],
        "returns": returns,
        "curve": curve
    }

# =========================================================
# 📈 CHART
# =========================================================
def chart(curve):

    fig, ax = plt.subplots(figsize=(10,5))
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    x = np.arange(len(curve))
    y = np.array(curve)

    ax.plot(x, y, color="#60a5fa", linewidth=2)
    ax.fill_between(x, y, color="#60a5fa", alpha=0.2)

    ax.grid(True, alpha=0.2)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    img = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return img

# =========================================================
# 🌐 ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()
    is_premium = False

    if request.method == "POST":

        monthly = float(request.form.get("monthly", 0))
        years = int(request.form.get("years", 1))

        normal = simulate(monthly, years, "normal")
        bull = simulate(monthly, years, "bull")
        bear = simulate(monthly, years, "bear")

        data = {
            "normal": normal,
            "bull": bull,
            "bear": bear
        }

        return render_template(
            "index.html",
            data=data,
            chart_normal=chart(normal["curve"]),
            chart_bull=chart(bull["curve"]),
            chart_bear=chart(bear["curve"]),
            is_premium=True
        )

    return render_template("index.html", data=None, is_premium=False)

# =========================================================
# 🚀 RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
