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
# 🔐 CONFIG
# =========================================================
ADMIN_PASSWORD = "Jobura@542542"
DB_FILE = "users.json"

# =========================================================
# 📦 SAFE USER SYSTEM
# =========================================================
def load_users():
    if not os.path.exists(DB_FILE):
        return []

    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        clean = []
        for u in data:
            if isinstance(u, dict) and "code" in u:
                clean.append(u)

        return clean

    except:
        return []


def save_users(users):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except:
        pass


def is_active(user):
    return (
        isinstance(user, dict)
        and "status" in user
        and (
            "monthly" in user.get("status", "")
            or "yearly" in user.get("status", "")
        )
    )


# =========================================================
# 💳 PAYMENT INFO
# =========================================================
PAYMENT_INFO = {
    "paybill": "542542",
    "account_number": "31909",
    "account_name": "Jobura Solutions"
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
# 🧠 AI ENGINE (RESTORED + SAFE)
# =========================================================
def ai_portfolio_advisor(weights, sim, assets):
    insights = []

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1)

    risk = float(np.mean(vol) * 100)
    score = float(max(0, 100 - risk * 10))

    for i in range(len(weights)):
        if weights[i] > 0.30:
            insights.append(f"High allocation: {assets[i][0]}")
        if vol[i] > np.mean(vol):
            insights.append(f"High volatility: {assets[i][0]}")
        if mean[i] < 0:
            insights.append(f"Weak returns: {assets[i][0]}")

    return {
        "insights": insights,
        "score": round(score, 2),
        "risk": round(risk, 2)
    }


# =========================================================
# 📊 SIMULATION ENGINE (STABLE)
# =========================================================
def simulate(monthly, years, mode="normal"):

    R = np.random.randn(N, 300) * 0.01
    weights = np.ones(N) / N

    months = max(int(years * 12), 1)
    invested = monthly * months

    nav = invested
    curve = []

    for t in range(months):
        idx = t % 300
        port_ret = np.dot(weights, R[:, idx])

        nav = nav * (1 + port_ret) + monthly
        curve.append(nav)

    return {
        "summary": {
            "invested": invested,
            "value": nav,
            "dividends": invested * 0.05
        },
        "curve": curve,
        "ai": ai_portfolio_advisor(weights, R, ASSETS)
    }


# =========================================================
# 📊 CHART
# =========================================================
def chart(curve):
    if not curve:
        return None

    fig, ax = plt.subplots()
    ax.plot(curve)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)

    return base64.b64encode(buf.read()).decode()


# =========================================================
# 🌐 MAIN ROUTE (PRODUCTION SAFE)
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()

    is_premium = False
    data = None
    normal = None

    try:

        if request.method == "POST":

            monthly = float(request.form.get("monthly") or 0)
            years = int(request.form.get("years") or 1)
            code = request.form.get("transaction_code", "").strip().upper()
            phone = request.form.get("phone", "").strip()

            # premium check
            for u in users:
                if u.get("code") == code and is_active(u):
                    is_premium = True

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

            # register user safely
            if code and not any(u.get("code") == code for u in users):
                users.append({
                    "code": code,
                    "phone": phone,
                    "status": "pending",
                    "plan": "",
                    "expiry": ""
                })
                save_users(users)

        return render_template(
            "index.html",
            data=data,
            chart_normal=chart(normal["curve"]) if normal else None,
            chart_bull=chart(data["bull"]["curve"]) if is_premium and data and data["bull"] else None,
            chart_bear=chart(data["bear"]["curve"]) if is_premium and data and data["bear"] else None,
            is_premium=is_premium,
            payment=PAYMENT_INFO
        )

    except Exception as e:
        return f"APP ERROR: {str(e)}"


# =========================================================
# 🚀 RENDER SAFE RUN
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
