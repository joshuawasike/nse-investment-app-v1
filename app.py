# ==========================================================
# JOBURA WEALTH®
# NSE Institutional Wealth Management Platform
# Professional Analytics Suite
# Version 2026
# ==========================================================

# ==========================================================
# FLASK
# ==========================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

# ==========================================================
# STANDARD LIBRARIES
# ==========================================================

import os
import io
import json
import glob
import random
import base64

from datetime import datetime

# ==========================================================
# DATA SCIENCE
# ==========================================================

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ==========================================================
# ENGINE MODULES
# ==========================================================

from engine.simulation import simulate_market

from engine.portfolio import build_portfolio

from engine.analytics import portfolio_summary

from engine.ai import investment_advisor

from engine.research import (
    company_database,
    ASSETS,
    DIVIDEND_DATABASE,
    DIVIDEND_BASE,
    load_data,
    get_df,
    estimate_market_statistics,
    get_market_stats,
    get_model_assets,
    estimate_dividend_yields
)

from engine.risk import portfolio_risk

from engine.retirement import retirement_projection

from engine.reports import create_report

from engine.utils import (
    load_json,
    save_json,
    today,
    money,
    percent,
    platform
)
# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

app.secret_key = "JOBURA_WEALTH_2026"

# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

STATIC_DIR = os.path.join(BASE_DIR, "static")

# ==========================================================
# JSON DATABASE FILES
# ==========================================================

USERS_FILE = "users.json"

COMPANIES_FILE = "companies.json"

DIVIDENDS_FILE = "dividends.json"

MARKET_FILE = "market_data.json"

MODELS_FILE = "portfolio_models.json"

SECTORS_FILE = "sectors.json"

AI_RULES_FILE = "ai_rules.json"

RISK_FILE = "risk_profiles.json"

ECONOMY_FILE = "economic_indicators.json"

SUBSCRIPTIONS_FILE = "subscriptions.json"

TRANSACTIONS_FILE = "transactions.json"

# ==========================================================
# LOAD DATABASES
# ==========================================================

companies = load_json(
    os.path.join(DATA_DIR, COMPANIES_FILE)
)

users = load_json(
    os.path.join(DATA_DIR, USERS_FILE)
)

dividends = load_json(
    os.path.join(DATA_DIR, DIVIDENDS_FILE)
)

market = load_json(
    os.path.join(DATA_DIR, MARKET_FILE)
)

portfolio_models = load_json(
    os.path.join(DATA_DIR, MODELS_FILE)
)

sectors = load_json(
    os.path.join(DATA_DIR, SECTORS_FILE)
)

ai_rules = load_json(
    os.path.join(DATA_DIR, AI_RULES_FILE)
)

risk_profiles = load_json(
    os.path.join(DATA_DIR, RISK_FILE)
)

economic = load_json(
    os.path.join(DATA_DIR, ECONOMY_FILE)
)

subscriptions = load_json(
    os.path.join(DATA_DIR, SUBSCRIPTIONS_FILE)
)

transactions = load_json(
    os.path.join(DATA_DIR, TRANSACTIONS_FILE)
)

# ==========================================================
# PLATFORM INFORMATION
# ==========================================================

APP = platform()

# ==========================================================
# GLOBAL SETTINGS
# ==========================================================

COMMUNITY_PLAN = "Community Edition"

PROFESSIONAL_PLAN = "Professional Edition"

INSTITUTIONAL_PLAN = "Institutional Edition"

DEFAULT_MARKET = "Normal"

DEFAULT_MODEL = "Dividend"

CURRENCY = "KES"

# ==========================================================
# APPLICATION HOME
# ==========================================================

@app.route("/")
def home():

    return render_template(

        "dashboard.html",

        app=APP,

        companies=companies,

        market=market,

        user=session.get("user"),

        premium=session.get("premium", False)

    )

@app.route("/companies")
def company_list():

    files = glob.glob("NSE_data_all_stock_*.csv")

    if not files:
        return "No CSV files found"

    names = []

    for f in files:
        try:
            temp = pd.read_csv(f)

            temp.columns = temp.columns.astype(str).str.strip().str.upper()

            possible_cols = [
                "NAME",
                "COMPANY",
                "SECURITY",
                "SYMBOL",
                "STOCK",
                "ISSUER"
            ]

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
# ==========================================================
# SECURITY CONFIGURATION
# ==========================================================

ADMIN_PASSWORD = "Jobura@542542"

USERS_PATH = os.path.join(DATA_DIR, USERS_FILE)

# ==========================================================
# USER MANAGEMENT
# ==========================================================

def load_users():
    return load_json(USERS_PATH)


def save_users(users):
    save_json(USERS_PATH, users)


def is_active(user):

    if not isinstance(user, dict):
        return False

    status = user.get("status", "").lower()

    return (
        "monthly" in status
        or
        "yearly" in status
        or
        "professional" in status
        or
        "institutional" in status
    )

# ==========================================================
# PAYMENT CONFIGURATION
# ==========================================================

PAYMENT_INFO = {

    "paybill": "542542",

    "account": "31909",

    "business_name": "Jobura Solutions",

    "currency": "KES"

}

# ==========================================================
# SUBSCRIPTION PRICING
# ==========================================================

PRICING = {

    "Community": {
        "monthly": 0,
        "yearly": 0
    },

    "Professional": {
        "monthly": 400,
        "yearly": 4000
    },

    "Institutional": {
        "monthly": 2000,
        "yearly": 18000
    }

}
from engine.research import (
    load_data,
    get_df,
    estimate_market_statistics,
    get_market_stats,
    get_model_assets,
    estimate_dividend_yields
)

# =========================================================
# 🏦 CORPORATE ACTION DATABASE
# =========================================================

CORPORATE_ACTIONS = {

    "EQTY":{

        "split":0.01,
        "bonus":0.03,
        "rights":0.04,
        "buyback":0.01,
        "special_dividend":0.02

    },

    "KCB":{

        "split":0.01,
        "bonus":0.02,
        "rights":0.03,
        "buyback":0.02,
        "special_dividend":0.01

    },

    "COOP":{

        "split":0.00,
        "bonus":0.04,
        "rights":0.02,
        "buyback":0.01,
        "special_dividend":0.02

    },

    "SCOM":{

        "split":0.00,
        "bonus":0.01,
        "rights":0.01,
        "buyback":0.04,
        "special_dividend":0.05

    },

    "EABL":{

        "split":0.00,
        "bonus":0.02,
        "rights":0.01,
        "buyback":0.02,
        "special_dividend":0.04

    },

    "KEGN":{

        "split":0.00,
        "bonus":0.01,
        "rights":0.02,
        "buyback":0.01,
        "special_dividend":0.01

    },

    "NCBA":{

        "split":0.01,
        "bonus":0.02,
        "rights":0.03,
        "buyback":0.02,
        "special_dividend":0.02

    },

    "KQ":{

        "split":0.00,
        "bonus":0.00,
        "rights":0.08,
        "buyback":0.00,
        "special_dividend":0.00

    }

}
# =========================================================
# 🏦 CORPORATE ACTION ENGINE
# =========================================================

def apply_corporate_actions(capital, code):

    profile = CORPORATE_ACTIONS.get(code)

    if profile is None:
        return capital, 0.0

    bonus = 0.0

    # Bonus shares
    if np.random.rand() < profile["bonus"]:

        capital *= 1.10

    # Rights issue
    if np.random.rand() < profile["rights"]:

        capital *= 1.05

    # Share buyback
    if np.random.rand() < profile["buyback"]:

        capital *= 1.03

    # Stock split
    if np.random.rand() < profile["split"]:

        capital *= 1.00

    # Special dividend
    if np.random.rand() < profile["special_dividend"]:

        bonus = capital * 0.03

    return capital, bonus

   
    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------
    summary = {

        "invested": round(float(invested),2),

        "value": round(float(portfolio_value),2),

        "real_value": round(float(real_value),2),

        "dividends": round(total_dividends,2),

        "annual_return": round(annual_return*100,2),

        "cagr": round(cagr*100,2),

        "volatility": round(volatility*100,2),

        "sharpe": round(sharpe,2),

        "max_drawdown": round(max_drawdown*100,2)

    }

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------
    return {

        "summary": summary,

        "chart": chart(curve),

        "plan": plan,

        "curve": curve,

        "ai": ai,

        "assets": breakdown,
        
        "returns": returns_table
    }


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
