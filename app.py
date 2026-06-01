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
# 📂 USERS DATABASE
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
# 🔐 USER STATUS CHECK
# =========================================================
def is_active(user):
    status = user.get("status", "")
    return "monthly" in status or "yearly" in status


# =========================================================
# 📊 PAYMENT INFO
# =========================================================
PAYMENT_INFO = {
    "paybill": "542542",
    "account_number": "31909",
    "account_name": "Jobura Solutions",
}

# =========================================================
# 📊 DATA ENGINE
# =========================================================
df = pd.DataFrame(columns=["Code", "Date", "Previous"])
files = glob.glob("data/nse_csv/*.csv")

for file in files:
    try:
        temp = pd.read_csv(file, usecols=["Code", "Date", "Previous"])
        df = pd.concat([df, temp], ignore_index=True)
    except Exception as e:
        print(f"Skipping {file}: {e}")
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
# 🎯 GOAL PLANNING ENGINE (NEW FEATURE)
# =========================================================

def months_to_target(P, FV, r):
    if r == 0:
        return FV / P
    n = np.log((FV * r / P) + 1) / np.log(1 + r)
    return n


def contribution_to_target(FV, n, r):
    if r == 0:
        return FV / n
    return FV * r / ((1 + r) ** n - 1)

# =========================================================
# ENGINE
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


def dividend_engine(asset_investment):
    yields = np.array([a[2] for a in ASSETS])
    return asset_investment * yields


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

        asset_values = asset_investment * (1 + np.array(
        [0.08, 0.07, 0.075, 0.06, 0.055, 0.065, 0.05, 0.0]
    )) ** years

    result = {
        "summary": {
            "invested": invested_total,
            "value": nav,
            "dividends": float(np.sum(asset_dividends)),
            "monthly_income": float(np.sum(asset_dividends)) / max(months, 1),
            "annual_income": float(np.sum(asset_dividends)) / max(years, 1)
        },
        "plan": [
            {
                "name": ASSETS[i][0],
                "percent": round(weights[i] * 100, 2),
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
        "curve": curve,

        "ai": ai_portfolio_advisor(weights, sim, ASSETS)
    }

    return result
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
    "curve": curve,

# =========================================================
# 🧠 AI PORTFOLIO ADVISOR ENGINE (V2)
# =========================================================
   def ai_portfolio_advisor(weights, sim, assets):
    insights = []

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1)

    total_weight = np.sum(weights)

    # portfolio risk score
    risk_score = np.mean(vol) * 100

    # detect concentration risk
    for i in range(len(weights)):
        name = assets[i][0]

        if weights[i] > 0.30:
            insights.append(f"⚠ {name}: High allocation ({weights[i]*100:.1f}%) → concentration risk.")

        if vol[i] > np.mean(vol):
            insights.append(f"📊 {name}: Higher volatility than portfolio average.")

        if mean[i] < 0:
            insights.append(f"📉 {name}: Weak or negative simulated returns.")

    # portfolio-level advice
    if risk_score > 3:
        insights.append("⚠ Portfolio risk is HIGH — consider more diversification.")

    if weights[7] > 0.1:
        insights.append("💡 Kenya Airways exposure is risky (zero dividend asset).")

    if np.max(weights) > 0.4:
        insights.append("⚠ One asset dominates portfolio — reduce concentration.")

    # final AI score (0–100)
    score = 100 - min(80, risk_score * 10)

    return {
        "insights": insights,
        "score": round(score, 1),
        "risk": round(risk_score, 2)
    }

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
}

return result

# =========================================================
# 🔐 ADMIN ROUTES
# =========================================================
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    users = load_users()
    users = [u for u in users if isinstance(u, dict)]

    for u in users:
        u.setdefault("code", "")
        u.setdefault("phone", "")
        u.setdefault("status", "pending")
        u.setdefault("expiry", "")
        u.setdefault("plan", "")
        u.setdefault("type", "Individual")
        u.setdefault("amount", 0)
        u.setdefault("date", "")

    total_users = len(users)

    pending_users = len([
        u for u in users
        if u.get("status") == "pending"
    ])

    approved_monthly = len([
        u for u in users
        if "monthly" in u.get("status", "")
    ])

    approved_yearly = len([
        u for u in users
        if "yearly" in u.get("status", "")
    ])

    rejected_users = len([
        u for u in users
        if u.get("status") == "rejected"
    ])

    total_revenue = sum(
        float(u.get("amount", 0))
        for u in users
    )

    monthly_revenue = sum(
        float(u.get("amount", 0))
        for u in users
        if "monthly" in u.get("status", "")
    )

    yearly_revenue = sum(
        float(u.get("amount", 0))
        for u in users
        if "yearly" in u.get("status", "")
    )

    return render_template(
        "admin.html",
        users=users,
        total_users=total_users,
        pending_users=pending_users,
        approved_monthly=approved_monthly,
        approved_yearly=approved_yearly,
        rejected_users=rejected_users,
        total_revenue=total_revenue,
        monthly_revenue=monthly_revenue,
        yearly_revenue=yearly_revenue
    )

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

            membership_type = request.args.get(
                "type",
                u.get("type", "Individual")
            )

            if plan == "monthly":

                u["status"] = f"{membership_type.lower()}_monthly"
                u["plan"] = "Monthly"

                if membership_type == "Institutional":
                    u["amount"] = 2000
                else:
                    u["amount"] = 400

            else:

                u["status"] = f"{membership_type.lower()}_yearly"
                u["plan"] = "Yearly"

                if membership_type == "Institutional":
                    u["amount"] = 18000
                else:
                    u["amount"] = 4000

            u["type"] = membership_type
            u["expiry"] = "ACTIVE"
            u["date"] = datetime.now().strftime("%Y-%m-%d")

            break

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
# MAIN ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()
    is_premium = False
    data = None
    goal_result = None

    if request.method == "POST":

        monthly = float(request.form.get("monthly", 0))
        years = int(request.form.get("years", 1))
        target = float(request.form.get("target_amount", 0))
        code = request.form.get("transaction_code", "").strip().upper()
        phone = request.form.get("phone", "").strip()

        r = 0.008

        # PREMIUM CHECK
        for u in users:
            if u.get("code") == code and is_active(u):
                is_premium = True

        # GOAL ENGINE
        if target > 0 and monthly > 0:
            months_needed = months_to_target(monthly, target, r)
            goal_result = {
                "mode": "time_to_goal",
                "years": round(months_needed / 12, 2)
            }

        elif target > 0 and years > 0:
            required_monthly = contribution_to_target(target, years * 12, r)
            goal_result = {
                "mode": "required_contribution",
                "monthly": round(required_monthly, 2)
            }

        # SIMULATION
        normal = simulate(monthly, years, "normal")

        if not is_premium:
            data = {"normal": normal, "bull": None, "bear": None}
        else:
            data = {
                "normal": normal,
                "bull": simulate(monthly, years, "bull"),
                "bear": simulate(monthly, years, "bear")
            }

        # USER REGISTRATION
        if code:
            if not any(u.get("code") == code for u in users):
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
            chart_normal=chart(normal["curve"]),
            chart_bull=chart(data["bull"]["curve"]) if is_premium and data["bull"] else None,
            chart_bear=chart(data["bear"]["curve"]) if is_premium and data["bear"] else None,
            is_premium=is_premium,
            payment=PAYMENT_INFO,
            goal_result=goal_result
        )

    return render_template(
        "index.html",
        data=None,
        is_premium=False,
        payment=PAYMENT_INFO,
        goal_result=None
    )

    # GET REQUEST
    return render_template(
        "index.html",
        data=None,
        is_premium=False,
        payment=PAYMENT_INFO,
        goal_result=None
    )

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
