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
# 🧠 MODEL → REAL COMPANY MAPPING (FIXED SAFE VERSION)
# =========================================================
def get_model_assets(model):

    df = get_df()

    if df is None or df.empty or "CODE" not in df.columns:
        return ASSETS[:8]

    df = df.copy()
    df["CODE"] = df["CODE"].astype(str).str.upper().str.strip()

    grouped = df.groupby("CODE")["PREVIOUS"].agg(["mean", "std"]).reset_index()
    grouped = grouped.dropna()

    grouped["return_score"] = grouped["mean"]
    grouped["risk_score"] = grouped["std"] + 1e-9
    grouped["sharpe_like"] = grouped["return_score"] / grouped["risk_score"]

    MODEL_UNIVERSES = {
        "dividend": ["EQTY", "KCB", "COOP", "EABL"],
        "growth":   ["SCOM", "KQ", "NCBA", "KEGN"],
        "banking":  ["EQTY", "KCB", "COOP", "NCBA"],
        "value":    ["EABL", "KEGN", "SCOM", "KQ"],
        "income":   ["EABL", "COOP", "KCB", "SCOM"]
    }

    allowed = MODEL_UNIVERSES.get(model, [])

    if allowed:
        grouped = grouped[grouped["CODE"].isin(allowed)]

    if grouped.empty:
        grouped = df.groupby("CODE")["PREVIOUS"].agg(["mean", "std"]).reset_index()
        grouped["return_score"] = grouped["mean"]
        grouped["risk_score"] = grouped["std"] + 1e-9
        grouped["sharpe_like"] = grouped["return_score"] / grouped["risk_score"]

    def bias(code):
        return 1.2 if code in allowed else 1.0

    grouped["score"] = grouped["sharpe_like"] * grouped["bias"]

    grouped = grouped.sort_values("score", ascending=False).head(len(ASSETS))

    # IMPORTANT: keep SAME structure as ASSETS (8 slots always)
    assets = [
        (row["CODE"], row["CODE"], float(np.random.uniform(0.04, 0.12)))
        for _, row in grouped.iterrows()
    ]

    # PAD to 8 to prevent broadcast errors
    while len(assets) < len(ASSETS):
        assets.append(ASSETS[len(assets)])

    return assets    
# =========================================================
# 🎯 APPLY MODEL BIAS TO WEIGHTS
# =========================================================
def apply_model_bias(weights, model):

    w = np.array(weights, dtype=float)

    # safety fix
    if len(w) == 0:
        return w

    if model == "dividend":
        target = np.array([0.20, 0.18, 0.15, 0.10, 0.15, 0.12, 0.08, 0.02])

    elif model == "growth":
        target = np.array([0.08, 0.08, 0.08, 0.25, 0.08, 0.08, 0.10, 0.25])

    elif model == "banking":
        target = np.array([0.25, 0.22, 0.20, 0.05, 0.05, 0.05, 0.15, 0.03])

    elif model == "value":
        target = np.array([0.08, 0.08, 0.08, 0.05, 0.12, 0.20, 0.12, 0.27])

    elif model == "income":
        target = np.array([0.10, 0.15, 0.15, 0.10, 0.25, 0.15, 0.08, 0.02])

    else:
        target = np.ones(len(w))

    # adjust size safety
    target = target[:len(w)]

    # blend
    w = (0.3 * w) + (0.7 * target)

    # normalize
    w = w / np.sum(w)

    return w
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

    w = np.array(weights, dtype=float)

    if len(w) < 8:
        return w / np.sum(w)

    # =====================================================
    # DIVIDEND MODEL
    # =====================================================
    if model == "dividend":

        target = np.array([
            0.20,  # EQTY
            0.18,  # KCB
            0.15,  # COOP
            0.10,  # SCOM
            0.15,  # EABL
            0.12,  # KEGN
            0.08,  # NCBA
            0.02   # KQ
        ])

    # =====================================================
    # GROWTH MODEL
    # =====================================================
    elif model == "growth":

        target = np.array([
            0.08,
            0.08,
            0.08,
            0.25,
            0.08,
            0.08,
            0.10,
            0.25
        ])

    # =====================================================
    # BANKING MODEL
    # =====================================================
    elif model == "banking":

        target = np.array([
            0.25,
            0.22,
            0.20,
            0.05,
            0.05,
            0.05,
            0.15,
            0.03
        ])

    # =====================================================
    # VALUE MODEL
    # =====================================================
    elif model == "value":

        target = np.array([
            0.08,
            0.08,
            0.08,
            0.05,
            0.12,
            0.20,
            0.12,
            0.27
        ])

    # =====================================================
    # INCOME MODEL
    # =====================================================
    elif model == "income":

        target = np.array([
            0.10,
            0.15,
            0.15,
            0.10,
            0.25,
            0.15,
            0.08,
            0.02
        ])

    else:
        target = np.ones(len(w))

    # blend optimizer with model identity
    w = (0.30 * w) + (0.70 * target)

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
# 🌍 MARKET GENERATOR (CLEAN + REGIME CONSISTENT)
# =========================================================
def generate_market(mode, N, drift, vol, momentum):

    base = np.random.randn(N, 300)

    # =====================================================
    # 📊 REGIME ADJUSTMENT (CORE DRIVER)
    # =====================================================
    if mode == "bull":
        drift *= 1.8
        vol *= 0.65
        shock_mult = 0.8
        bias = 0.004

    elif mode == "bear":
        drift *= 0.55
        vol *= 1.6
        shock_mult = 1.4
        bias = -0.004

    else:
        shock_mult = 1.0
        bias = 0.0
    # =====================================================
    # 📊 CORE MARKET STRUCTURE
    # =====================================================

    trend = drift + (base * vol * momentum)

    mean_reversion = -0.004 * np.cumsum(base, axis=1)

    shock = (
        np.random.standard_t(5, size=(N, 300))
        * vol
        * 0.2
        * shock_mult
    )

    R = trend + mean_reversion + shock

    # =====================================================
    # 📊 REGIME ALIGNMENT FIX (CRITICAL STABILITY LAYER)
    # =====================================================
    R = R + bias

    # hard safety clamp (prevents cross-model explosions)
    R = np.clip(R, -0.20, 0.30)

    return R
    # =====================================================
    # 📈 RETURN COMPONENTS
    # =====================================================
    trend = drift + (base * vol * momentum)
    mean_reversion = -0.004 * np.cumsum(base, axis=1)
    shock = np.random.standard_t(5, size=(N, 300)) * vol * 0.2 * shock_mult

    R = trend + mean_reversion + shock

    # =====================================================
    # ⚖️ REGIME ALIGNMENT (MUST BE INSIDE FUNCTION)
    # =====================================================
    R = R + bias

    # =====================================================
    # 🛡️ SAFETY CLAMP
    # =====================================================
    return np.clip(R, -0.20, 0.30)
# =========================================================
# 🧠 AI PORTFOLIO ADVISOR (ADD HERE)
# =========================================================
def ai_portfolio_advisor(weights, R, assets):

    avg_returns = np.mean(R, axis=1)
    risk = np.std(avg_returns)

    top_idx = int(np.argmax(weights))
    top_asset = assets[top_idx][0]

    if risk < 0.01:
        comment = "Low risk environment. Defensive portfolio."
    elif risk < 0.02:
        comment = "Moderate risk. Balanced exposure."
    else:
        comment = "High volatility. Consider reducing risk."

    return {
        "top_asset": top_asset,
        "risk_level": float(risk),
        "commentary": comment
    }
# =========================================================
# 🏦 REGIME-CONSISTENT INSTITUTIONAL ALLOCATOR (FIXED)
# =========================================================
def institutional_allocator(sim, mode):

    # =====================================================
    # 📊 CORE STATISTICS
    # =====================================================
    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9
    downside = np.mean(np.minimum(sim, 0), axis=1)

    sharpe = mean / vol
    sortino = mean / (np.abs(downside) + 1e-9)

    # =====================================================
    # 🧠 COMPOSITE SCORE
    # =====================================================
    score = (0.7 * sharpe) + (0.3 * sortino)

    # =====================================================
    # 🌍 REGIME ADJUSTMENT
    # =====================================================
    regime_map = {
        "normal": 1.0,
        "bull": 1.25,
        "bear": 0.65
    }

    score = score * regime_map.get(mode, 1.0)

    # =====================================================
    # 🔧 STRUCTURAL TILTS
    # =====================================================
    if len(score) > 3:
        score[3] *= 1.15

    if len(score) > 7:
        score[7] *= 0.10

    # =====================================================
    # 🔥 NORMALIZATION
    # =====================================================
    score = np.tanh(score * 2.2)

    weights = np.exp(score)
    weights = weights / np.sum(weights)

    # =====================================================
    # 🛡️ SAFETY CLIPPING (FIXED ERROR HERE)
    # =====================================================
    n = len(weights)

    MIN = np.full(n, 0.04)
    MAX = np.full(n, 0.40)

    weights = np.clip(weights, MIN, MAX)

    return weights / np.sum(weights)
# =========================================================
# 🧠 PATH SIMULATION (MISSING FUNCTION FIX)
# =========================================================
def simulate_paths(R, mode):

    REGIME = {
        "normal": {"mu": 0.0025, "vol": 1.0},
        "bull":   {"mu": 0.0055, "vol": 1.2},
        "bear":   {"mu": -0.0035, "vol": 1.3},
    }

    cfg = REGIME.get(mode, REGIME["normal"])
    N = R.shape[0]
    T = R.shape[1]

    sim = []

    for i in range(N):
        base_vol = np.std(R[i]) + 1e-9
        series = []

        for t in range(T):
            shock = np.random.standard_t(5) * base_vol * cfg["vol"]
            step = R[i][t] + cfg["mu"] + shock

            if mode == "bear":
                step = np.clip(step, -0.05, 0.01)

            series.append(step)

        sim.append(series)

    return np.array(sim)

def simulate(monthly, years, mode, model="dividend"):

    # =========================================================
    # 🧠 MODEL PARAMETERS
    # =========================================================
    model_params = {
        "dividend": (0.0035, 0.012, 0.60),
        "growth":   (0.0060, 0.022, 1.10),
        "banking":  (0.0045, 0.016, 0.80),
        "value":    (0.0040, 0.015, 0.75),
        "income":   (0.0038, 0.013, 0.70),
    }

    drift_base, vol_base, momentum = model_params.get(model, (0.001, 0.01, 0.6))

    regime = {
        "normal": (1.0, 1.0),
        "bull":   (1.9, 0.7),
        "bear":   (0.55, 1.5)
    }

    drift_mult, vol_mult = regime.get(mode, (1.0, 1.0))

    drift = drift_base * drift_mult
    vol = vol_base

    # =========================================================
    # 🌍 MARKET GENERATOR (CLEAN + REGIME CONSISTENT)
    # =========================================================
    R_full = generate_market(mode, len(ASSETS), drift, vol, momentum)

    # =========================================================
    # 🧠 MODEL ASSET SELECTION
    # =========================================================
    base_assets = get_model_assets(model)

    MODEL_UNIVERSES = {
        "dividend": ["Equity Bank", "KCB Group", "Co-op Bank", "EABL"],
        "growth":   ["Safaricom", "Kenya Airways", "NCBA", "KenGen"],
        "banking":  ["Equity Bank", "KCB Group", "Co-op Bank", "NCBA"],
        "value":    ["EABL", "KenGen", "Safaricom"],
        "income":   ["EABL", "Co-op Bank", "KCB Group", "Safaricom"]
    }

    if model in MODEL_UNIVERSES:
        allowed = MODEL_UNIVERSES[model]
        assets = [a for a in base_assets if a[0] in allowed]
    else:
        assets = base_assets

    if not assets:
        assets = ASSETS[:6]

    # =========================================================
    # 🔥 SAFE INDEX ALIGNMENT (CRITICAL FIX)
    # =========================================================
    asset_names = [a[0] for a in ASSETS]
    selected_names = [a[0] for a in assets]

    selected_idx = []
    for name in selected_names:
        if name in asset_names:
            selected_idx.append(asset_names.index(name))

    if len(selected_idx) < 2:
        selected_idx = list(range(min(6, len(ASSETS))))

    R = R_full[selected_idx]

    assets = assets[:len(selected_idx)]

    # =========================================================
    # 🧠 INSTITUTIONAL WEIGHTS
    # =========================================================
    sim = R
    weights = institutional_allocator(sim, mode)
    weights = apply_model_bias(weights, model)

    # =========================================================
    # 💰 PORTFOLIO SIMULATION (MAIN LOOP)
    # =========================================================
    months = years * 12
    invested = monthly * months

    nav = invested
    curve = []

    for t in range(months):

        idx = t % R.shape[1]

        if t % 12 == 0:
            sim = R
            weights = institutional_allocator(sim, mode)
            weights = apply_model_bias(weights, model)

        port_ret = np.dot(weights, R[:, idx])

        port_ret = np.clip(
            port_ret,
            -0.05 if mode == "bear" else -0.03,
            0.08 if mode == "bull" else 0.05
        )

        nav = nav * (1 + port_ret)
        nav += monthly * (1 + 0.0005)

        curve.append(nav)

# =========================================================
# 💰 DIVIDENDS (MONTHLY FLOW MODEL - FIXED)
# =========================================================
dividends = np.zeros(len(weights))
yields = np.array([a[2] for a in assets])

for t in range(months):

    # monthly allocation into each asset
    monthly_allocation = monthly * weights

    # accumulate dividends per asset over time
    dividends += monthly_allocation * yields
    # =========================================================
    # 📈 PORTFOLIO VALUE MODEL
    # =========================================================
    base_returns = np.mean(R, axis=1)
    annual_returns = np.clip(base_returns * 12, -0.25, 0.45)

    asset_values = np.array([
        asset_investment[i] * max(0.5, (1 + annual_returns[i]) ** years)
        for i in range(len(assets))
    ])

    portfolio_value = float(np.sum(asset_values))

    # =========================================================
    # 📊 PLAN OUTPUT
    # =========================================================
    plan = [
        {
            "name": assets[i][0],
            "percent": round(weights[i] * 100, 2),
            "kes": round(asset_investment[i], 2)
        }
        for i in range(len(assets))
    ]

    # =========================================================
    # 🤖 AI INSIGHT ENGINE
    # =========================================================
    risk = float(np.std(np.mean(R, axis=1)))

    ai = {
        "top_asset": assets[int(np.argmax(weights))][0],
        "risk_level": risk,
        "commentary": (
            "Low risk environment." if risk < 0.01 else
            "Moderate risk environment." if risk < 0.02 else
            "High volatility detected."
        )
    }

    # =========================================================
    # 📦 OUTPUT (FINAL RETURN - DO NOT MOVE)
    # =========================================================
    return {
        "summary": {
            "invested": float(invested),
            "value": float(portfolio_value),
            "dividends": float(np.sum(dividends))
        },
        "chart": chart(curve),
        "plan": plan,
        "curve": curve,
        "ai": ai
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
    best_model_name = None
    best_model_value = 0
    ranking = []

    try:

        if request.method == "POST":

            # INPUTS
            monthly = float(request.form.get("monthly") or 0)
            years = int(request.form.get("years") or 1)
            target_amount = float(request.form.get("target_amount") or 0)

            # GOAL ANALYSIS
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

            # RUN ALL MODELS
            models = [
                "dividend",
                "growth",
                "banking",
                "value",
                "income"
            ]

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

            # SAVE NEW USER
            if code and not any(u.get("code") == code for u in users):

                users.append({
                    "code": code,
                    "phone": phone,
                    "status": "pending",
                    "plan": "all_models",
                    "expiry": ""
                })

                save_users(users)

            # BEST MODEL
            for model_name, result in data.items():

                try:
                    value = result["normal"]["summary"]["value"]

                    if value > best_model_value:
                        best_model_value = value
                        best_model_name = model_name

                except:
                    pass

            # MODEL RANKING
            ranking = sorted(
                data.items(),
                key=lambda x: x[1]["normal"]["summary"]["value"],
                reverse=True
            )

        return render_template(
            "index.html",
            data=data,
            goal_result=goal_result,
            is_premium=is_premium,
            best_model_name=best_model_name,
            best_model_value=best_model_value,
            ranking=ranking
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
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
