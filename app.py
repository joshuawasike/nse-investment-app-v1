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


def is_active(user):

    status = user.get("status", "")

   def is_active(user):
    status = user.get("status", "")
    return "approved" in status


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
# 🔐 ADMIN
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

    return render_template("admin.html", users=users)


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

            membership_type = request.args.get("type", "Individual")

if plan == "monthly":
    u["status"] = f"{membership_type.lower()}_monthly"
    u["plan"] = "Monthly"
else:
    u["status"] = f"{membership_type.lower()}_yearly"
    u["plan"] = "Yearly"

u["type"] = membership_type
u["expiry"] = "ACTIVE"

            u["expiry"] = "ACTIVE"

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
# MAIN FIXED LOGIC
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    users = load_users()
    is_premium = False
    data = None

    if request.method == "POST":

        monthly = float(request.form.get("monthly", 0))
        years = int(request.form.get("years", 1))
        code = request.form.get("transaction_code", "").strip().upper()
        phone = request.form.get("phone", "").strip()

        for u in users:
            if u.get("code") == code and is_active(u):
                is_premium = True

        normal = simulate(monthly, years, "normal")

        # 🔥 FIX: FREE = ONLY NORMAL
        if not is_premium:
            data = {
                "normal": normal,
                "bull": None,
                "bear": None
            }
        else:
            data = {
                "normal": normal,
                "bull": simulate(monthly, years, "bull"),
                "bear": simulate(monthly, years, "bear")
            }

        # 🔥 STORE USER FOR ADMIN APPROVAL
        if code:
            if not any(u.get("code") == code for u in users):
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
            chart_normal=chart(normal["curve"]),
            chart_bull=chart(data["bull"]["curve"]) if is_premium else None,
            chart_bear=chart(data["bear"]["curve"]) if is_premium else None,
            is_premium=is_premium,
            payment=PAYMENT_INFO
        )

    return render_template("index.html", data=None, is_premium=False, payment=PAYMENT_INFO)


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
