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
# 📂 USERS DATABASE (SAFE VERSION)
# =========================================================
DB_FILE = "users.json"


def load_users():
    """Safe JSON loader (prevents production crashes)"""
    if not os.path.exists(DB_FILE):
        return []

    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except:
        return []


def save_users(users):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except:
        pass


# =========================================================
# 📊 PAYMENT INFO
# =========================================================
PAYMENT_INFO = {
    "paybill": "542542",
    "account_number": "31909",
    "account_name": "Jobura Solutions",
}

# =========================================================
# 📊 DATA LOADING (SAFE)
# =========================================================
df = pd.DataFrame(columns=["Code", "Date", "Previous"])
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
# RETURNS ENGINE
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
# SIMULATION ENGINE
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
# OPTIMIZER
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

    MIN = np.array([0.03,0.03,0.03,0.10,0.03,0.03,0.03,0.00])
    MAX = np.array([0.25,0.25,0.25,0.40,0.20,0.20,0.20,0.05])

    weights = np.clip(weights, MIN, MAX)
    return weights / np.sum(weights)


# =========================================================
# DIVIDENDS
# =========================================================
def dividend_engine(asset_investment):
    yields = np.array([a[2] for a in ASSETS])
    return asset_investment * yields


# =========================================================
# SIMULATION WRAPPER
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

        if t % 6 == 0:
            weights = optimize(sim)

    asset_investment = invested_total * weights
    asset_dividends = dividend_engine(asset_investment)

    asset_values = asset_investment * (1 + np.array(
        [0.08,0.07,0.075,0.06,0.055,0.065,0.05,0.0]
    )) ** years

    return {
        "summary": {
            "invested": invested_total,
            "value": nav,
            "dividends": float(np.sum(asset_dividends)),
            "monthly_income": float(np.sum(asset_dividends)) / max(months,1),
            "annual_income": float(np.sum(asset_dividends)) / max(years,1)
        },
        "plan": [
            {
                "name": ASSETS[i][0],
                "percent": round(weights[i]*100,2),
                "kes": round(monthly*weights[i],2)
            }
            for i in range(N)
        ],
        "returns": [
            {
                "name": ASSETS[i][0],
                "dividends": round(asset_dividends[i],2),
                "value": round(asset_values[i],2)
            }
            for i in range(N)
        ],
        "curve": curve
    }


# =========================================================
# CHART
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
# 🔐 ADMIN PANEL (FIXED - NO MORE 500 ERRORS)
# =========================================================
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    try:
        users = load_users()
        return render_template("admin.html", users=users)

    except Exception as e:
        return f"ADMIN ERROR SAFE MODE: {str(e)}"


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password"

    return """
    <form method="POST">
        <input name="password" type="password" placeholder="Admin Password">
        <button type="submit">Login</button>
    </form>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/approve/<code>/<plan>")
def approve(code, plan):

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    for u in users:
        if u.get("code") == code:
            u["status"] = "approved"
            u["plan"] = plan

            days = 30 if plan == "monthly" else 365
            u["expiry"] = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    save_users(users)
    return redirect("/admin")


@app.route("/reject/<code>")
def reject(code):

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    for u in users:
        if u.get("code") == code:
            u["status"] = "rejected"

    save_users(users)
    return redirect("/admin")


# =========================================================
# MAIN ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()
    is_premium = False

    if request.method == "POST":

        monthly = float(request.form.get("monthly", 0))
        years = int(request.form.get("years", 1))
        code = request.form.get("transaction_code", "").strip().upper()

        for u in users:
            if u.get("code") == code and u.get("status") == "approved":
                if "expiry" in u:
                    if datetime.now() < datetime.strptime(u["expiry"], "%Y-%m-%d"):
                        is_premium = True

        normal = simulate(monthly, years, "normal")

        data = {
            "normal": normal,
            "bull": simulate(monthly, years, "bull"),
            "bear": simulate(monthly, years, "bear")
        }

        return render_template(
            "index.html",
            data=data,
            chart_normal=chart(normal["curve"]),
            chart_bull=chart(data["bull"]["curve"]),
            chart_bear=chart(data["bear"]["curve"]),
            is_premium=is_premium,
            payment=PAYMENT_INFO
        )

    return render_template("index.html", data=None, is_premium=False, payment=PAYMENT_INFO)


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
