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
app.secret_key = "jobura_secure_secure_v3"

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
        with open(DB_FILE, "w") as f:
            json.dump([], f)
        return []

    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        return [u for u in data if isinstance(u, dict)]

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
# 📊 SIMULATION ENGINE
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

    yields = np.array([a[2] for a in ASSETS])
    dividends = asset_investment * yields

    asset_values = asset_investment * (1 + np.array(
        [0.08,0.07,0.075,0.06,0.055,0.065,0.05,0.0]
    )) ** years

    return {
        "summary": {
            "invested": invested,
            "value": nav,
            "dividends": float(np.sum(dividends))
        },

        "plan": [
            {
                "name": ASSETS[i][0],
                "percent": round(weights[i] * 100, 2),
                "kes": round(asset_investment[i], 2)
            }
            for i in range(N)
        ],

        "returns": [
            {
                "name": ASSETS[i][0],
                "dividends": round(dividends[i], 2),
                "value": round(asset_values[i], 2)
            }
            for i in range(N)
        ],

        "curve": curve,
        "ai": ai_portfolio_advisor(weights, R, ASSETS)
    }

# =========================================================
# 📊 CHART
# =========================================================
def chart(curve):
    fig, ax = plt.subplots(figsize=(10, 5))

    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    x = np.arange(len(curve))
    y = np.array(curve)

    ax.plot(x, y, color="#60a5fa", linewidth=2)
    ax.fill_between(x, y, color="#60a5fa", alpha=0.15)

    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#334155")
    ax.spines["left"].set_color("#334155")
    ax.spines["top"].set_color("#0b0f19")
    ax.spines["right"].set_color("#0b0f19")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)

    plt.close(fig)

    return base64.b64encode(buf.read()).decode()

# =========================================================
# 🔐 LOGIN
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password"

    return """
    <form method="POST" style="padding:20px;">
        <input name="password" type="password" placeholder="Admin Password">
        <button type="submit">Login</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# =========================================================
# 🎯 GOAL PLANNER
# =========================================================
def years_to_goal(monthly, target, annual_return=0.10):

    if monthly <= 0 or target <= 0:
        return None

    monthly_rate = annual_return / 12

    balance = 0
    months = 0

    while balance < target and months < 1200:
        balance = balance * (1 + monthly_rate) + monthly
        months += 1

    return round(months / 12, 1)


def monthly_for_goal(target, years, annual_return=0.10):

    if target <= 0 or years <= 0:
        return None

    r = annual_return / 12
    n = years * 12

    factor = ((1 + r) ** n - 1) / r

    monthly = target / factor

    return round(monthly, 0)
# =========================================================
# 🌐 MAIN ROUTE
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

    target_amount = float(
        request.form.get("target_amount") or 0
    )

    if target_amount > 0:

goal_result = {
    "target": target_amount,
    "current_monthly": monthly,
    "years_needed": years_to_goal(monthly, target_amount),
    "monthly_5": monthly_for_goal(target_amount, 5),
    "monthly_10": monthly_for_goal(target_amount, 10),
    "monthly_15": monthly_for_goal(target_amount, 15)
}

    code = request.form.get(
        "transaction_code", ""
    ).strip().upper()

    phone = request.form.get(
        "phone", ""
    ).strip()

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
        data = {
            "normal": normal,
            "bull": None,
            "bear": None
        }

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
            goal_result=goal_result,
            chart_normal=chart(normal["curve"]) if normal else None,
            chart_bull=chart(data["bull"]["curve"]) if is_premium and data and data["bull"] else None,
            chart_bear=chart(data["bear"]["curve"]) if is_premium and data and data["bear"] else None,
            is_premium=is_premium,
            payment=PAYMENT_INFO
        )

    except Exception as e:
        return f"APP ERROR: {str(e)}"

# =========================================================
# 🚀 ADMIN ROUTE (FIXED SAFE)
# =========================================================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    safe_users = []
    for u in users:
        if isinstance(u, dict):
            safe_users.append(u)

    return render_template(
        "admin.html",
        users=safe_users,
        total_users=len(safe_users),
        pending_users=len([u for u in safe_users if u.get("status") == "pending"]),
        approved_monthly=len([u for u in safe_users if u.get("status") == "approved_monthly"]),
        approved_yearly=len([u for u in safe_users if u.get("status") == "approved_yearly"]),
        rejected_users=len([u for u in safe_users if u.get("status") == "rejected"]),
        monthly_revenue=0,
        yearly_revenue=0,
        total_revenue=0
    )
# =========================================================
# ✅ APPROVE USER
# =========================================================
@app.route("/approve/<code>/<plan>")
def approve(code, plan):

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    for u in users:

        if u.get("code") == code:

            if plan == "monthly":
                u["status"] = "approved_monthly"
                u["plan"] = "Monthly"

            elif plan == "yearly":
                u["status"] = "approved_yearly"
                u["plan"] = "Yearly"

            u["expiry"] = "ACTIVE"

    save_users(users)

    return redirect("/admin")


# =========================================================
# ❌ REJECT USER
# =========================================================
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
# 🔄 CANCEL SUBSCRIPTION
# =========================================================
@app.route("/cancel/<code>")
def cancel(code):

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()

    for u in users:

        if u.get("code") == code:
            u["status"] = "pending"
            u["plan"] = ""
            u["expiry"] = ""

    save_users(users)

    return redirect("/admin")
# =========================================================
# 🚀 RUN (RENDER SAFE)
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
