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
@app.route("/companies")
def companies():

    files = glob.glob("NSE_data_all_stock_*.csv")

    if not files:
        return "No CSV files found"

    names = []

    for f in files:
        try:
            temp = pd.read_csv(f)

            # normalize column names
            temp.columns = temp.columns.astype(str).str.strip().str.upper()

            # possible name columns (VERY IMPORTANT FIX)
            possible_cols = ["NAME", "COMPANY", "SECURITY", "SYMBOL", "STOCK", "ISSUER"]

            name_col = None
            for col in temp.columns:
                if col in possible_cols:
                    name_col = col
                    break

            if name_col is None:
                continue

            names.extend(
                temp[name_col]
                .dropna()
                .astype(str)
                .str.upper()
                .str.strip()
                .tolist()
            )

        except Exception:
            continue

    if not names:
        return "No valid company names found"

    return "<br>".join(sorted(set(names)))
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
            temp = pd.read_csv(file)

            # normalize columns
            temp.columns = temp.columns.astype(str).str.strip().str.upper()

            # only keep safe columns if they exist
            keep = [c for c in ["CODE", "DATE", "PREVIOUS"] if c in temp.columns]

            if len(keep) == 0:
                continue

            temp = temp[keep]

            df_local = pd.concat([df_local, temp], ignore_index=True)

        except Exception:
            continue

    # FINAL CLEANING
    if not df_local.empty:
        df_local["DATE"] = pd.to_datetime(df_local["DATE"], errors="coerce")
        df_local["PREVIOUS"] = pd.to_numeric(df_local["PREVIOUS"], errors="coerce")
        df_local = df_local.dropna()

    return df_local


def get_df():
    global df
    if df is None:
        df = load_data()
    return df
# =========================================================
# 🧠 MODEL → REAL COMPANY MAPPING (IMPROVED VERSION)
# =========================================================
def get_model_assets(model):

    df = get_df()

    if df is None or df.empty or "CODE" not in df.columns:
        return ASSETS[:8]

    df = df.copy()
    df["CODE"] = df["CODE"].astype(str).str.upper().str.strip()

    # =========================================================
    # 📊 BASIC PERFORMANCE ENGINE
    # =========================================================
    grouped = df.groupby("CODE")["PREVIOUS"].agg(["mean", "std"]).reset_index()
    grouped = grouped.dropna()

    grouped["return_score"] = grouped["mean"]
    grouped["risk_score"] = grouped["std"] + 1e-9
    grouped["sharpe_like"] = grouped["return_score"] / grouped["risk_score"]

    # =========================================================
    # 🧠 MODEL UNIVERSES (HARD SEGMENTATION - KEY FIX)
    # =========================================================
    model_universe = {
        "dividend": ["EABL","KCB","EQTY","COOP","KEGN","SCOM","KPLC","BAT"],
        "growth":   ["NCBA","SCOM","KQ","ARM","KCB","EQTY","COOP"],
        "banking":  ["KCB","EQTY","COOP","NCBA","DTB","SBM"],
        "value":    ["NMG","KPLC","KEGN","EABL","COOP","KCB"],
        "income":   ["EABL","BAT","KPLC","SCOM","COOP","KCB"]
    }

    allowed = model_universe.get(model, None)

    # =========================================================
    # 🧠 FILTER UNIVERSE (VERY IMPORTANT FIX)
    # =========================================================
    if allowed is not None:
        grouped = grouped[grouped["CODE"].isin(allowed)]

    # fallback safety
    if grouped.empty:
        grouped = df.groupby("CODE")["PREVIOUS"].agg(["mean","std"]).reset_index()
        grouped["return_score"] = grouped["mean"]
        grouped["risk_score"] = grouped["std"] + 1e-9
        grouped["sharpe_like"] = grouped["return_score"] / grouped["risk_score"]

    # =========================================================
    # 🎯 STRONG MODEL BIAS (NOW STRUCTURALLY MEANINGFUL)
    # =========================================================
    def model_bias(code):

        code = str(code)

        if model == "dividend":
            return 1.6 if code in ["EABL","KCB","COOP","KEGN"] else 1.1

        elif model == "growth":
            return 1.7 if code in ["NCBA","SCOM","KQ"] else 1.0

        elif model == "banking":
            return 1.8 if code in ["KCB","EQTY","COOP","NCBA"] else 0.7

        elif model == "value":
            return 1.5 if code in ["NMG","KPLC","KEGN"] else 0.9

        elif model == "income":
            return 1.6 if code in ["EABL","BAT","KPLC"] else 1.0

        return 1.0

    grouped["bias"] = grouped["CODE"].apply(model_bias)

    # =========================================================
    # 🧠 FINAL SCORE (NOW MEANINGFULLY DIFFERENT PER MODEL)
    # =========================================================
    grouped["score"] = (
        grouped["sharpe_like"] * grouped["bias"]
    )

    # =========================================================
    # 🏆 TOP PICKS WITH DIVERSITY CONTROL
    # =========================================================
    grouped = grouped.sort_values("score", ascending=False)

    selected = []
    used = set()

    for _, row in grouped.iterrows():

        code = row["CODE"]

        # prevent duplicates inside same run
        if code in used:
            continue

        selected.append(row)
        used.add(code)

        if len(selected) == 8:
            break

    # =========================================================
    # 📦 OUTPUT FORMAT (UNCHANGED INTERFACE)
    # =========================================================
    assets = [
        (
            r["CODE"],   # name
            r["CODE"],   # symbol
            np.random.uniform(0.04, 0.12)
        )
        for r in selected
    ]

    return assets
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
def optimize_weights(sim, mode="normal"):

    n = sim.shape[0]

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9
    downside = np.mean(np.minimum(sim, 0), axis=1)

    # =========================================================
    # RISK PARITY
    # =========================================================
    inv_vol = 1.0 / vol
    rp_weights = inv_vol / np.sum(inv_vol)

    # =========================================================
    # ALPHA SCORE (SAFE DYNAMIC VERSION)
    # =========================================================
    safe_ratio = mean / (vol + 1e-9)
    score = safe_ratio - (1.1 * np.abs(downside))

    # NO FIXED INDEXING LIKE score[7]
    alpha = np.tanh(score * 2.0)
    alpha_weights = np.exp(alpha - np.max(alpha))
    alpha_weights = alpha_weights / np.sum(alpha_weights)

    # =========================================================
    # HYBRID
    # =========================================================
    w = 0.55 * rp_weights + 0.45 * alpha_weights

    # =========================================================
    # REGIME TILT (SAFE)
    # =========================================================
    if mode == "bull":
        w *= 1.05
    elif mode == "bear":
        w *= 0.95

    # =========================================================
    # NORMALIZATION
    # =========================================================
    w = np.maximum(w, 1e-6)
    w = w / np.sum(w)

    # =========================================================
    # DYNAMIC CLIP (NO FIXED SIZE ARRAYS)
    # =========================================================
    MIN = np.full(n, 0.03)
    MAX = np.full(n, 0.40)

    w = np.clip(w, MIN, MAX)
    w = w / np.sum(w)

    return w
def apply_model_bias(weights, model):

    w = weights.copy()
    n = len(w)

    def safe(i, factor):
        if i < n:
            w[i] *= factor

    if model == "dividend":
        for i, f in enumerate([1.1, 1.1, 1.1, 1.2, 1.15]):
            safe(i, f)

    elif model == "growth":
        for i, f in enumerate([2.0, 1.2, 1.2, 1.1, 1.1]):
            safe(i, f)

    elif model == "banking":
        for i, f in enumerate([1.3, 1.3, 1.2, 1.2]):
            safe(i, f)

    elif model == "value":
        for i, f in enumerate([1.2, 1.2, 1.3, 1.1]):
            safe(i, f)

    elif model == "income":
        for i, f in enumerate([1.2, 1.2, 1.1, 1.1]):
            safe(i, f)

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
# 📊 SIMULATION ENGINE (STABLE + REALISTIC MARKET FIX)
# =========================================================
def simulate(monthly, years, mode, model="dividend"):

    # =========================================================
    # 🧠 GET MODEL ASSETS
    # =========================================================
    assets = get_model_assets(model)
    N_local = len(assets)

    if N_local == 0:
        assets = ASSETS[:4]
        N_local = len(assets)

    # =========================================================
    # 🧠 MODEL MARKET PERSONALITY
    # =========================================================
    model_params = {
        "dividend": (0.0010, 0.008, 0.6),
        "growth":   (0.0030, 0.018, 1.2),
        "banking":  (0.0015, 0.010, 0.8),
        "value":    (0.0010, 0.012, 0.7),
        "income":   (0.0012, 0.009, 0.5),
    }

    drift_base, vol_base, momentum = model_params.get(model, (0.001, 0.01, 0.6))

    # =========================================================
    # 🌪️ REGIME ADJUSTMENT
    # =========================================================
    regime_multiplier = {
        "normal": 1.0,
        "bull": 1.15,
        "bear": 0.85
    }.get(mode, 1.0)

    drift = drift_base * regime_multiplier
    vol = vol_base * regime_multiplier

    # =========================================================
    # 📊 MARKET GENERATION (STABLE + BOUNDED)
    # =========================================================
    base = np.random.randn(N_local, 300)

    # controlled trend (IMPORTANT FIX)
    trend = np.cumsum(base * 0.3, axis=1) * (vol * momentum)

    # fat-tail shocks (CAPPED)
    shock = np.random.standard_t(5, size=(N_local, 300)) * vol * 0.25

    R = drift + trend + shock

    # =========================================================
    # 🚨 HARD SAFETY CLAMP (CRITICAL FIX)
    # prevents trillion/quadrillion explosions
    # =========================================================
    R = np.clip(R, -0.08, 0.08)

    # =========================================================
    # 🧠 MODEL BOOST (SMOOTHED)
    # =========================================================
    model_boost = {
        "dividend": 0.95,
        "growth": 1.25,
        "banking": 1.05,
        "value": 0.90,
        "income": 0.92
    }.get(model, 1.0)

    R *= model_boost

    # =========================================================
    # 🧠 WEIGHTS
    # =========================================================
    weights = optimize_weights(R, mode)
    weights = apply_model_bias(weights, model)

    # =========================================================
    # 📊 SIMULATION LOOP (STABLE COMPOUNDING FIX)
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

        # 🚨 HARD RETURN LIMIT (CRITICAL FIX)
        port_ret = np.clip(port_ret, -0.05, 0.06)

        # safer compounding
        nav = nav * (1 + port_ret)

        # add contribution AFTER growth
        nav += monthly

        curve.append(nav)

    # =========================================================
    # 💰 ASSET BREAKDOWN
    # =========================================================
    asset_investment = invested * weights

    yields = np.array([a[2] for a in assets])
    dividends = asset_investment * yields

    base_returns = np.linspace(0.05, 0.09, N_local)
    asset_values = asset_investment * (1 + base_returns) ** years

    # =========================================================
    # 📦 OUTPUT
    # =========================================================
    return {
        "summary": {
            "invested": invested,
            "value": float(np.clip(nav, 0, 1e12)),  # FINAL SAFETY CAP
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

            # INPUTS
            monthly = float(request.form.get("monthly") or 0)
            years = int(request.form.get("years") or 1)
            model = request.form.get("model", "dividend")
            target_amount = float(request.form.get("target_amount") or 0)

            # GOAL
            if target_amount > 0:
                goal_result = {
                    "target": target_amount,
                    "current_monthly": monthly,
                    "years_needed": years_to_goal(monthly, target_amount),
                    "monthly_5": monthly_for_goal(target_amount, 5),
                    "monthly_10": monthly_for_goal(target_amount, 10),
                    "monthly_15": monthly_for_goal(target_amount, 15)
                }

            # USER CHECK
            code = request.form.get("transaction_code", "").strip().upper()
            phone = request.form.get("phone", "").strip()

            for u in users:
                if u.get("code") == code and is_active(u):
                    is_premium = True

            # RUN MODELS
            models = ["dividend", "growth", "banking", "value", "income"]

            for m in models:
                normal = simulate(monthly, years, "normal", m)

                if is_premium:
                    bull = simulate(monthly, years, "bull", m)
                    bear = simulate(monthly, years, "bear", m)
                else:
                    bull = None
                    bear = None

                data[m] = {
                    "normal": normal,
                    "bull": bull,
                    "bear": bear
                }

            # STORE USER
            if code and not any(u.get("code") == code for u in users):
                users.append({
                    "code": code,
                    "phone": phone,
                    "status": "pending",
                    "plan": "all_models",
                    "expiry": ""
                })
                save_users(users)

        return render_template(
            "index.html",
            data=data,
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
