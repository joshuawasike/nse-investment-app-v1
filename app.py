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

        return [u for u in data if isinstance(u, dict)]

    except:
        return []


def save_users(users):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except:
        pass


# =========================================================
# 🔐 SAFE CHECKS
# =========================================================
def is_active(user):
    return isinstance(user, dict) and (
        "monthly" in user.get("status", "") or "yearly" in user.get("status", "")
    )


def months_to_target(P, FV, r):
    return np.log((FV * r / P) + 1) / np.log(1 + r) if r != 0 else FV / P


def contribution_to_target(FV, n, r):
    return FV * r / ((1 + r) ** n - 1) if r != 0 else FV / n


# =========================================================
# 📊 PAYMENT INFO
# =========================================================
PAYMENT_INFO = {
    "paybill": "542542",
    "account_number": "31909",
    "account_name": "Jobura Solutions"
}

# =========================================================
# 📊 DATA ENGINE
# =========================================================
df = None


def load_data():
    df_local = pd.DataFrame(columns=["Code", "Date", "Previous"])
    files = glob.glob("data/nse_csv/*.csv")

    for file in files:
        try:
            temp = pd.read_csv(file, usecols=["Code", "Date", "Previous"])
            df_local = pd.concat([df_local, temp], ignore_index=True)
        except:
            continue

    if not df_local.empty:
        df_local["Date"] = pd.to_datetime(df_local["Date"], errors="coerce")
        df_local["Previous"] = pd.to_numeric(df_local["Previous"], errors="coerce")
        df_local = df_local.dropna()

    return df_local


def get_df():
    global df
    if df is None:
        df = load_data()
    return df


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
# 🧠 AI ENGINE
# =========================================================
def ai_portfolio_advisor(weights, sim, assets):
    insights = []
    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1)

    for i in range(len(weights)):
        if weights[i] > 0.3:
            insights.append(f"High allocation: {assets[i][0]}")
        if vol[i] > np.mean(vol):
            insights.append(f"High volatility: {assets[i][0]}")
        if mean[i] < 0:
            insights.append(f"Weak returns: {assets[i][0]}")

    return {
        "insights": insights,
        "score": float(max(0, 100 - np.mean(vol) * 10)),
        "risk": float(np.mean(vol) * 100)
    }


# =========================================================
# 📊 SIMULATION CORE
# =========================================================
def simulate(monthly, years, mode):

    R = np.random.randn(N, 300) * 0.01
    weights = np.ones(N) / N

    months = years * 12
    invested = monthly * months

    nav = invested
    curve = []

    for t in range(months):
        idx = t % 300
        port_ret = np.dot(weights, R[:, idx])

        nav = nav * (1 + port_ret) + monthly
        curve.append(nav)

    asset_investment = invested * weights

    return {
        "summary": {
            "invested": invested,
            "value": nav,
            "dividends": float(np.sum(asset_investment) * 0.05)
        },
        "curve": curve,
        "ai": ai_portfolio_advisor(weights, R, ASSETS)
    }


# =========================================================
# 📊 CHART
# =========================================================
def chart(curve):
    fig, ax = plt.subplots()
    ax.plot(curve)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)

    return base64.b64encode(buf.read()).decode()


# =========================================================
# 🌐 ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()

    is_premium = False
    data = None
    normal = None
    goal_result = None

    try:

        if request.method == "POST":

            monthly = float(request.form.get("monthly") or 0)
            years = int(request.form.get("years") or 1)
            target = float(request.form.get("target_amount") or 0)

            code = request.form.get("transaction_code", "").strip().upper()
            phone = request.form.get("phone", "").strip()

            # premium check
            for u in users:
                if u.get("code") == code and is_active(u):
                    is_premium = True

            # goal engine
            if target > 0 and monthly > 0:
                goal_result = {
                    "mode": "time_to_goal",
                    "years": round(months_to_target(monthly, target, 0.008) / 12, 2)
                }

            # simulation
            normal = simulate(monthly, years, "normal")

            if is_premium:
                data = {
                    "normal": normal,
                    "bull": simulate(monthly, years, "bull"),
                    "bear": simulate(monthly, years, "bear")
                }
            else:
                data = {
                    "normal": normal,
                    "bull": None,
                    "bear": None
                }

            # register user
            if code and not any(u.get("code") == code for u in users):
                users.append({
                    "code": code,
                    "phone": phone,
                    "status": "pending"
                })
                save_users(users)

        return render_template(
            "index.html",
            data=data,
            chart_normal=chart(normal["curve"]) if normal else None,
            chart_bull=chart(data["bull"]["curve"]) if is_premium and data and data.get("bull") else None,
            chart_bear=chart(data["bear"]["curve"]) if is_premium and data and data.get("bear") else None,
            is_premium=is_premium,
            payment=PAYMENT_INFO,
            goal_result=goal_result
        )

    except Exception as e:
        return f"APP ERROR: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
