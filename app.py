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
@app.route("/companies")
def companies():

    import pandas as pd
    import glob

    # =========================================================
# 📊 LOAD NSE DATA (ALL YEARS)
# =========================================================
files = glob.glob("NSE_data_all_stock_*.csv")

df = pd.concat([pd.read_csv(f) for f in files])

# IMPORTANT: normalize company names
df["NAME"] = df["NAME"].str.upper().str.strip()

    return "<br>".join(companies)
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
# 💰 PRICING CONFIG (ADD THIS HERE)
# =========================================================
PRICING = {
    "monthly": 400,
    "yearly": 4000
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
# 🧠 MODEL → REAL COMPANY MAPPING (STEP 4A GOES HERE)
# =========================================================
def get_model_assets(model):
    df = get_df()

    model_map = {
        "dividend": ["SAFARICOM", "KCB", "EQUITY", "CO-OP", "NCBA", "EABL", "KENGEN", "BAT"],
        "growth": ["KENYA AIRWAYS", "CARBACID", "CIC", "JUBILEE", "STANBIC", "DIAMOND TRUST", "I&M", "ABSA"],
        "banking": ["EQUITY", "KCB", "NCBA", "I&M", "STANBIC", "DIAMOND TRUST", "ABSA", "CO-OP"],
        "value": ["BAMBURI", "KENYA RE", "NMG", "CIC", "TPS SERENA", "KENYA POWER", "CENTUM", "LONGHORN"],
        "income": ["BAT", "EABL", "SAFARICOM", "KENGEN", "STANBIC", "NCBA", "CO-OP", "KCB"]
    }

    selected = model_map.get(model, [])

    assets = []
    for name in selected:
        row = df[df["NAME"].str.contains(name, na=False)]
        if not row.empty:
            assets.append((name.title(), name[:5], 0.07))

    return assets if assets else ASSETS
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
# 🧠 MODEL COMPANIES (REAL CSV-BASED FILTERING)
# =========================================================

MODEL_COMPANIES = {
    "dividend": [
        "SAFARICOM",
        "KCB GROUP",
        "EQUITY BANK",
        "CO-OP BANK",
        "NCBA BANK",
        "EABL",
        "KENGEN",
        "BAT"
    ],

    "growth": [
        "KENYA AIRWAYS",
        "CARBACID",
        "CIC INSURANCE",
        "JUBILEE HOLDINGS",
        "STANBIC",
        "DIAMOND TRUST BANK",
        "I&M BANK",
        "ABSA BANK"
    ],

    "banking": [
        "EQUITY BANK",
        "KCB GROUP",
        "NCBA BANK",
        "I&M BANK",
        "STANBIC",
        "DIAMOND TRUST BANK",
        "ABSA BANK",
        "CO-OP BANK"
    ],

    "value": [
        "BAMBURI CEMENT",
        "KENYA RE",
        "NATION MEDIA GROUP",
        "CIC INSURANCE",
        "TPS SERENA",
        "KENYA POWER",
        "CENTUM",
        "LONGHORN"
    ],

    "income": [
        "BAT",
        "EABL",
        "SAFARICOM",
        "KENGEN",
        "STANBIC",
        "NCBA BANK",
        "CO-OP BANK",
        "KCB GROUP"
    ]
}
# =========================================================
# 🧠 AI ENGINE
# =========================================================
def optimize_weights(sim, mode="normal"):

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9
    downside = np.mean(np.minimum(sim, 0), axis=1)

    # =========================================================
    # RISK-PARITY BASE
    # =========================================================
    inv_vol = 1.0 / vol
    rp_weights = inv_vol / np.sum(inv_vol)

    # =========================================================
    # ALPHA SIGNAL (STABILIZED)
    # =========================================================
    safe_ratio = mean / (vol + 1e-9)
    score = safe_ratio - (1.1 * np.abs(downside))

    score[3] *= 1.2
    score[7] *= 0.05

    alpha = np.tanh(score * 2.0)
    alpha_weights = np.exp(alpha - np.max(alpha))
    alpha_weights = alpha_weights / np.sum(alpha_weights)

    # =========================================================
    # HYBRID BLEND
    # =========================================================
    w = 0.55 * rp_weights + 0.45 * alpha_weights

    # =========================================================
    # REGIME TILT
    # =========================================================
    if mode == "bull":
        w[3] *= 1.15
        w[1] *= 1.05

    elif mode == "bear":
        w[7] *= 0.3
        w[4] *= 0.85

    # =========================================================
    # SAFETY NORMALIZATION (IMPORTANT FIX)
    # =========================================================
    w = np.maximum(w, 1e-6)
    w = w / np.sum(w)

    # =========================================================
    # HARD CONSTRAINTS
    # =========================================================
    MIN = np.array([0.03,0.03,0.03,0.10,0.03,0.03,0.03,0.00])
    MAX = np.array([0.25,0.25,0.25,0.40,0.20,0.20,0.20,0.05])

    w = np.clip(w, MIN, MAX)
    w = w / np.sum(w)

    return w
def apply_model_bias(weights, model):

    w = weights.copy()

    # DIVIDEND BLUE CHIP
    if model == "dividend":
        w[3] *= 1.2
        w[0] *= 1.1
        w[1] *= 1.1
        w[2] *= 1.1
        w[4] *= 1.15

    # GROWTH
    elif model == "growth":
        w[7] *= 2.0
        w[5] *= 1.2
        w[6] *= 1.2

    # BANKING
    elif model == "banking":
        w[0] *= 1.3
        w[1] *= 1.3
        w[2] *= 1.2
        w[6] *= 1.2

    # VALUE
    elif model == "value":
        w[5] *= 1.2
        w[6] *= 1.2
        w[7] *= 1.3
        w[4] *= 1.1

    # INCOME
    elif model == "income":
        w[3] *= 1.2
        w[4] *= 1.2
        w[1] *= 1.1
        w[0] *= 1.1

    # FINAL NORMALIZATION SAFETY
    w = np.maximum(w, 1e-6)
    w = w / np.sum(w)

    return w
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
MODEL_UNIVERSES = {
    "dividend": [0,1,2,3,4,5,6],   # safe banks + blue chips
    "growth":   [7,5,6,1,2,3,4],   # includes KQ aggressively
    "banking":  [0,1,2,6,3],       # only banks + safaricom
    "value":    [5,6,7,4],         # cyclical + recovery stocks
    "income":   [3,4,1,0,2]        # dividend-heavy names
}
# =========================================================
# 📊 SIMULATION ENGINE (FIXED + MODEL-SPECIFIC UNIVERSES)
# =========================================================
def simulate(monthly, years, mode, model="dividend"):

    # =========================================================
    # 🧠 GET MODEL ASSETS (FROM CSV FILTER)
    # =========================================================
    assets = get_model_assets(model)
    N_local = len(assets)

    # fallback safety
    if N_local == 0:
        assets = ASSETS
        N_local = len(assets)

    # =========================================================
    # 🌪️ RETURN GENERATION
    # =========================================================
    base = np.random.randn(N_local, 300)

    if mode == "normal":
        drift = 0.0005
        vol = 0.010
    elif mode == "bull":
        drift = 0.0035
        vol = 0.014
    elif mode == "bear":
        drift = -0.0035
        vol = 0.020
    else:
        drift = 0.0005
        vol = 0.010

    R = base * vol + drift

    # fat-tail shocks
    shock = np.random.standard_t(4, size=(N_local, 300)) * vol * 0.5
    R += shock

    # =========================================================
    # 🧠 SMART WEIGHTS
    # =========================================================
    base_weights = optimize_weights(R, mode)
    base_weights = apply_model_bias(base_weights, model)

    weights = base_weights.copy()

    # =========================================================
    # 📊 SIMULATION LOOP
    # =========================================================
    months = years * 12
    invested = monthly * months

    nav = invested
    curve = []

    for t in range(months):
        idx = t % 300

        if t % 6 == 0:
            w = optimize_weights(R, mode)
            w = apply_model_bias(w, model)
            weights = w

        port_ret = np.dot(weights, R[:, idx])
        nav = nav * (1 + port_ret) + monthly
        curve.append(nav)

    # =========================================================
    # 💰 ASSET BREAKDOWN
    # =========================================================
    asset_investment = invested * weights

    yields = np.array([a[2] for a in assets])
    dividends = asset_investment * yields

    asset_values = asset_investment * (1 + np.array(
        [0.08, 0.07, 0.075, 0.06, 0.055, 0.065, 0.05, 0.0][:N_local]
    )) ** years

    # =========================================================
    # 📦 RESULT OUTPUT
    # =========================================================
    return {
        "summary": {
            "invested": invested,
            "value": nav,
            "dividends": float(np.sum(dividends))
        },

        "plan": [
            {
                "name": assets[i][0],
                "percent": round(weights[i] * 100, 2),
                "kes": round(asset_investment[i], 2)
            }
            for i in range(N_local)
        ],

        "returns": [
            {
                "name": assets[i][0],
                "dividends": round(dividends[i], 2),
                "value": round(asset_values[i], 2)
            }
            for i in range(N_local)
        ],

        "curve": curve,
        "ai": ai_portfolio_advisor(weights, R, assets)
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
    data = {}
    goal_result = None

    try:
        if request.method == "POST":

            # =========================================================
            # INPUTS
            # =========================================================
            monthly = float(request.form.get("monthly") or 0)
            years = int(request.form.get("years") or 1)
            model = request.form.get("model", "dividend")  # default, we will loop for all
            target_amount = float(request.form.get("target_amount") or 0)

            # =========================================================
            # GOAL PLANNER
            # =========================================================
            if target_amount > 0:
                goal_result = {
                    "target": target_amount,
                    "current_monthly": monthly,
                    "years_needed": years_to_goal(monthly, target_amount),
                    "monthly_5": monthly_for_goal(target_amount, 5),
                    "monthly_10": monthly_for_goal(target_amount, 10),
                    "monthly_15": monthly_for_goal(target_amount, 15)
                }

            # =========================================================
            # USER CHECK
            # =========================================================
            code = request.form.get("transaction_code", "").strip().upper()
            phone = request.form.get("phone", "").strip()

            for u in users:
                if u.get("code") == code and is_active(u):
                    is_premium = True

            # =========================================================
            # RUN ALL MODELS
            # =========================================================
            models = ["dividend", "growth", "banking", "value", "income"]
            for m in models:
                # Run simulation for each scenario (normal, bull, bear)
                normal = simulate(monthly, years, "normal", model=m)
                if is_premium:
                    bull = simulate(monthly, years, "bull", model=m)
                    bear = simulate(monthly, years, "bear", model=m)
                    data[m] = {
                        "normal": normal,
                        "bull": bull,
                        "bear": bear
                    }
                else:
                    data[m] = {
                        "normal": normal,
                        "bull": None,
                        "bear": None
                    }

# =========================================================
# STORE USER (if new code)
# =========================================================
if code and not any(u.get("code") == code for u in users):

    users.append({
        "code": code,
        "phone": phone,
        "status": "pending",
        "plan": "all_models",
        "expiry": ""
    })

    save_users(users)
        # =========================================================
        # RENDER (PASS ALL MODELS FOR COMPARISON)
        # =========================================================
        return render_template(
            "index.html",
            data=data,  # All models stored here
            goal_result=goal_result,
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

    safe_users = [u for u in users if isinstance(u, dict)]

    monthly_users = len([u for u in safe_users if u.get("status") == "approved_monthly"])
    yearly_users = len([u for u in safe_users if u.get("status") == "approved_yearly"])

    monthly_revenue = monthly_users * PRICING["monthly"]
    yearly_revenue = yearly_users * PRICING["yearly"]

    total_revenue = monthly_revenue + yearly_revenue

    return render_template(
        "admin.html",
        users=safe_users,
        total_users=len(safe_users),
        pending_users=len([u for u in safe_users if u.get("status") == "pending"]),
        approved_monthly=monthly_users,
        approved_yearly=yearly_users,
        rejected_users=len([u for u in safe_users if u.get("status") == "rejected"]),
        monthly_revenue=monthly_revenue,
        yearly_revenue=yearly_revenue,
        total_revenue=total_revenue
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
