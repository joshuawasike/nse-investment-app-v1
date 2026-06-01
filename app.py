from datetime import datetime
from flask import Flask, render_template, request, redirect, session
import pandas as pd
import numpy as np
import glob
import matplotlib
import json
import os
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
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []


def save_users(users):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except:
        pass


# =========================================================
# 🔐 USER STATUS
# =========================================================
def is_active(user):
    return "monthly" in user.get("status", "") or "yearly" in user.get("status", "")


# =========================================================
# 📊 PAYMENT INFO
# =========================================================
PAYMENT_INFO = {
    "paybill": "542542",
    "account_number": "31909",
    "account_name": "Jobura Solutions",
}

# =========================================================
# 📊 DATA ENGINE (SAFE LAZY LOAD)
# =========================================================
df = None

def load_data():
    df_local = pd.DataFrame(columns=["Code", "Date", "Previous"])
    files = glob.glob("data/nse_csv/*.csv")

    for file in files:
        try:
            temp = pd.read_csv(file, usecols=["Code", "Date", "Previous"])
            df_local = pd.concat([df_local, temp], ignore_index=True)
        except Exception as e:
            print(f"Skipping {file}: {e}")

    if not df_local.empty:
        df_local["Date"] = pd.to_datetime(df_local["Date"], errors="coerce")
        df_local["Previous"] = pd.to_numeric(df_local["Previous"], errors="coerce")
        df_local = df_local.dropna()
        df_local = df_local.sort_values(["Code", "Date"])

    return df_local


def get_df():
    global df
    if df is None:
        df = load_data()
    return df


# =========================================================
# 🎯 GOAL ENGINE
# =========================================================
def months_to_target(P, FV, r):
    if r == 0:
        return FV / P
    return np.log((FV * r / P) + 1) / np.log(1 + r)


def contribution_to_target(FV, n, r):
    if r == 0:
        return FV / n
    return FV * r / ((1 + r) ** n - 1)


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
# 📊 RETURNS ENGINE
# =========================================================
def get_returns():
    df_local = get_df()
    R = []

    for _, code, _ in ASSETS:
        px = df_local[df_local["Code"] == code]["Previous"].values
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
# 📊 SIMULATION
# =========================================================
def simulate_paths(R, mode):
    REGIME = {
        "normal": {"mu": 0.0025, "vol": 1.0},
        "bull": {"mu": 0.0055, "vol": 1.2},
        "bear": {"mu": -0.0035, "vol": 1.3},
    }

    cfg = REGIME.get(mode, REGIME["normal"])
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
# 📊 OPTIMIZER
# =========================================================
def optimize(sim):
    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9
    downside = np.mean(np.minimum(sim, 0), axis=1)

    score = (mean / vol) - (1.1 * np.abs(downside))
    score = np.tanh(score * 2.0)

    weights = np.exp(score)
    weights = weights / np.sum(weights)

    MIN = np.array([0.03,0.03,0.03,0.10,0.03,0.03,0.03,0.00])
    MAX = np.array([0.25,0.25,0.25,0.40,0.20,0.20,0.20,0.05])

    weights = np.clip(weights, MIN, MAX)
    return weights / np.sum(weights)


# =========================================================
# 📊 DIVIDENDS
# =========================================================
def dividend_engine(asset_investment):
    yields = np.array([a[2] for a in ASSETS])
    return asset_investment * yields


# =========================================================
# 📊 SIMULATION WRAPPER
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

    asset_values = asset_investment * (1 + np.array(
        [0.08,0.07,0.075,0.06,0.055,0.065,0.05,0.0]
    )) ** years

    return {
        "summary": {
            "invested": invested_total,
            "value": nav,
            "dividends": float(np.sum(asset_dividends))
        },
        "plan": [
            {
                "name": ASSETS[i][0],
                "percent": round(weights[i]*100, 2),
                "kes": round(monthly * weights[i], 2)
            }
            for i in range(N)
        ],
        "returns": [
            {
                "name": ASSETS[i][0],
                "dividends": round(asset_dividends[i], 2),
                "value": round(asset_values[i], 2)
            }
            for i in range(N)
        ],
        "curve": curve
    }


# =========================================================
# 📊 CHART
# =========================================================
def chart(curve):
    fig, ax = plt.subplots(figsize=(10,5))
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    x = np.arange(len(curve))
    y = np.array(curve)

    ax.plot(x, y, color="#60a5fa", linewidth=2)
    ax.fill_between(x, y, color="#60a5fa", alpha=0.15)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)

    img = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img


# =========================================================
# 🌐 MAIN ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()
    is_premium = False
    data = None
    goal_result = None
    normal = None

    try:
        if request.method == "POST":

            monthly = float(request.form.get("monthly") or 0)
            years = int(request.form.get("years") or 1)
            target = float(request.form.get("target_amount") or 0)
            code = request.form.get("transaction_code", "").strip().upper()
            phone = request.form.get("phone", "").strip()

            for u in users:
                if u.get("code") == code and is_active(u):
                    is_premium = True

            normal = simulate(monthly, years, "normal")

            if is_premium:
                data = {
                    "normal": normal,
                    "bull": simulate(monthly, years, "bull"),
                    "bear": simulate(monthly, years, "bear")
                }
            else:
                data = {"normal": normal, "bull": None, "bear": None}

            if code and not any(u.get("code") == code for u in users):
                users.append({
                    "code": code,
                    "phone": phone,
                    "status": "pending",
                    "plan": "",
                    "expiry": "",
                    "type": "Individual",
                    "amount": 0,
                    "date": ""
                })
                save_users(users)

        return render_template(
            "index.html",
            data=data,
            chart_normal=chart(normal["curve"]) if normal else None,
            chart_bull=chart(data["bull"]["curve"]) if is_premium and data else None,
            chart_bear=chart(data["bear"]["curve"]) if is_premium and data else None,
            is_premium=is_premium,
            payment=PAYMENT_INFO,
            goal_result=goal_result
        )

    except Exception as e:
        return f"APP ERROR: {str(e)}"


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
