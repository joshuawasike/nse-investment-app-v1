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

PAYMENT_INFO = {
    "paybill": "542542",
    "account_number": "31909",
    "account_name": "Jobura Solutions"
}

PRICING = {
    "monthly": 400,
    "yearly": 4000
}

# =========================================================
# 📦 USERS
# =========================================================
def load_users():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)
        return []

    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except:
        return []

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

def is_active(user):
    return user.get("status", "").startswith("approved")

# =========================================================
# 📊 DATA LOADER
# =========================================================
df_cache = None

def load_data():
    df_local = pd.DataFrame()

    files = glob.glob("data/nse_csv/*.csv")

    for file in files:
        try:
            temp = pd.read_csv(file)
            temp.columns = temp.columns.astype(str).str.strip().str.upper()

            keep = [c for c in ["CODE", "DATE", "PREVIOUS"] if c in temp.columns]
            if not keep:
                continue

            temp = temp[keep]
            df_local = pd.concat([df_local, temp], ignore_index=True)

        except:
            continue

    if not df_local.empty:
        df_local["DATE"] = pd.to_datetime(df_local["DATE"], errors="coerce")
        df_local["PREVIOUS"] = pd.to_numeric(df_local["PREVIOUS"], errors="coerce")
        df_local = df_local.dropna()

    return df_local

def get_df():
    global df_cache
    if df_cache is None:
        df_cache = load_data()
    return df_cache

# =========================================================
# 🧠 ASSETS
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

# =========================================================
# 📊 MARKET ENGINE (CLEAN FIXED)
# =========================================================
def generate_market(mode, N, drift, vol, momentum):

    base = np.random.randn(N, 300)

    if mode == "bull":
        drift *= 1.8
        vol *= 0.7
        shock_mult = 0.8
    elif mode == "bear":
        drift *= 0.6
        vol *= 1.6
        shock_mult = 1.4
    else:
        shock_mult = 1.0

    trend = drift + base * vol * momentum
    mean_reversion = -0.003 * np.cumsum(base, axis=1)
    shock = np.random.standard_t(6, size=(N, 300)) * vol * 0.2 * shock_mult

    R = trend + mean_reversion + shock
    return np.clip(R, -0.20, 0.25)

# =========================================================
# 🧠 WEIGHTS ENGINE
# =========================================================
def optimize_weights(sim, mode="normal"):
    n = sim.shape[0]

    mean = np.mean(sim, axis=1)
    vol = np.std(sim, axis=1) + 1e-9

    inv_vol = 1 / vol
    rp = inv_vol / np.sum(inv_vol)

    score = mean / vol
    alpha = np.exp(score - np.max(score))
    alpha = alpha / np.sum(alpha)

    w = 0.5 * rp + 0.5 * alpha

    if mode == "bull":
        w *= 1.05
    elif mode == "bear":
        w *= 0.95

    w = np.maximum(w, 1e-6)
    return w / np.sum(w)

# =========================================================
# 📊 SIMULATION ENGINE (FIXED)
# =========================================================
def simulate(monthly, years, mode, model="dividend"):

    assets = ASSETS[:8]
    N = len(assets)

    model_params = {
        "dividend": (0.0008, 0.006, 0.6),
        "growth": (0.0025, 0.015, 1.0),
        "banking": (0.0012, 0.009, 0.7),
        "value": (0.0010, 0.010, 0.6),
        "income": (0.0010, 0.007, 0.5),
    }

    drift, vol, momentum = model_params.get(model, (0.001, 0.01, 0.6))

    R = generate_market(mode, N, drift, vol, momentum)

    weights = optimize_weights(R, mode)

    months = years * 12
    invested = monthly * months

    nav = invested
    curve = []

    for t in range(months):
        idx = t % 300

        if t % 6 == 0:
            weights = optimize_weights(R, mode)

        port_ret = np.dot(weights, R[:, idx])
        port_ret = np.clip(port_ret, -0.03, 0.04)

        nav = max(nav * (1 + port_ret), 0)
        nav += monthly * 0.98

        curve.append(nav)

    asset_investment = invested * weights
    dividends = asset_investment * np.array([a[2] for a in assets])

    asset_values = asset_investment * (1.1 ** years)

    return {
        "summary": {
            "invested": invested,
            "value": float(np.sum(asset_values)),
            "dividends": float(np.sum(dividends))
        },
        "plan": [
            {
                "name": assets[i][0],
                "percent": round(weights[i] * 100, 2),
                "kes": round(asset_investment[i], 2)
            }
            for i in range(N)
        ],
        "curve": curve
    }

# =========================================================
# 🌐 ROUTES
# =========================================================
@app.route("/")
def index():
    return "App Running"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password"

    return "<form method='POST'><input name='password'><button>Login</button></form>"

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")
    return "Admin OK"

# =========================================================
# 🚀 RUN
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
