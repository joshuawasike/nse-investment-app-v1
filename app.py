"""
=========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform

Main Application Controller

Version 2.0
=========================================================
"""

# ==========================================================
# STANDARD LIBRARIES
# ==========================================================

import os
import json
import random
from datetime import datetime

import numpy as np
import pandas as pd

# ==========================================================
# FLASK
# ==========================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session
)

# ==========================================================
# ENGINE IMPORTS
# ==========================================================

from engine.simulation import simulate

from engine.portfolio import (
    build_portfolio
)

from engine.analytics import (
    portfolio_summary
)

from engine.risk import (
    portfolio_risk_report
)

from engine.ai import (
    investment_advisor
)

from engine.retirement import retirement_projection
)

from engine.reports import (
    generate_report
)

# ==========================================================
# APPLICATION
# ==========================================================

app = Flask(__name__)

# ==========================================================
# CONFIGURATION
# ==========================================================

app.config["SECRET_KEY"] = (
    "jobura-wealth-2026"
)

app.config["JSON_SORT_KEYS"] = False

# ==========================================================
# DATA PATHS
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

CSV_DIR = os.path.join(
    DATA_DIR,
    "nse_csv"
)

REPORT_DIR = os.path.join(
    BASE_DIR,
    "reports"
)

EXPORT_DIR = os.path.join(
    BASE_DIR,
    "exports"
)

# ==========================================================
# MEMBERSHIP
# ==========================================================

INDIVIDUAL_MONTHLY = 400

INDIVIDUAL_YEARLY = 4000

INSTITUTION_MONTHLY = 2000

INSTITUTION_YEARLY = 18000

# ==========================================================
# DEFAULT SETTINGS
# ==========================================================

DEFAULT_MODEL = "balanced"

DEFAULT_MODE = "normal"

DEFAULT_YEARS = 10

DEFAULT_MONTHLY = 10000

# ==========================================================
# COMPANY DATABASE
# ==========================================================

COMPANY_DATABASE = os.path.join(
    DATA_DIR,
    "companies.json"
)

DIVIDEND_DATABASE = os.path.join(
    DATA_DIR,
    "dividend_database.json"
)

USER_DATABASE = os.path.join(
    DATA_DIR,
    "users.json"
)

# ==========================================================
# APPLICATION INFORMATION
# ==========================================================

APP_INFO = {

    "platform":
        "JOBURA WEALTH®",

    "system":
        "NSE Institutional Wealth Management Platform",

    "version":
        "2.0",

    "developer":
        "Jobura Solutions",

    "year":
        "2026"

}
# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def load_json(filename):
    """
    Loads a JSON file safely.
    """

    if not os.path.exists(filename):
        return {}

    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    """
    Saves data to a JSON file.
    """

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4
        )


def money(value):
    """
    Currency formatting.
    """

    return f"KES {value:,.2f}"


def percent(value):
    """
    Percentage formatting.
    """

    return f"{value:.2f}%"


def today():

    return datetime.now().strftime(
        "%d %B %Y"
    )


# ==========================================================
# MEMBERSHIP
# ==========================================================

def membership_price(plan):

    plans = {

        "individual_monthly":
            INDIVIDUAL_MONTHLY,

        "individual_yearly":
            INDIVIDUAL_YEARLY,

        "institution_monthly":
            INSTITUTION_MONTHLY,

        "institution_yearly":
            INSTITUTION_YEARLY

    }

    return plans.get(plan, 0)


def load_users():

    return load_json(
        USER_DATABASE
    )


def save_users(users):

    save_json(
        USER_DATABASE,
        users
    )


# ==========================================================
# AUTHENTICATION
# ==========================================================

def authenticate(username, password):
    """
    Simple authentication.

    Can later be replaced with
    a database authentication system.
    """

    users = load_users()

    if username not in users:
        return False

    return users[username]["password"] == password


def current_user():

    return session.get("username")


def logged_in():

    return current_user() is not None


def logout_user():

    session.clear()


def login_user(username):

    session["username"] = username
# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():
    """
    Landing page.
    """
    return render_template(
        "index.html",
        app=APP_INFO
    )


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if authenticate(username, password):

            login_user(username)

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "danger"
        )

    return render_template(
        "login.html",
        app=APP_INFO
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(
        url_for("home")
    )


# ==========================================================
# DASHBOARD
# ==========================================================

@app.route("/dashboard")
def dashboard():

    if not logged_in():

        return redirect(
            url_for("login")
        )

    return render_template(

        "dashboard.html",

        app=APP_INFO,

        user=current_user()

    )


# ==========================================================
# MEMBERSHIP
# ==========================================================

@app.route("/membership")
def membership():

    plans = {

        "Individual Monthly":
            membership_price(
                "individual_monthly"
            ),

        "Individual Yearly":
            membership_price(
                "individual_yearly"
            ),

        "Institution Monthly":
            membership_price(
                "institution_monthly"
            ),

        "Institution Yearly":
            membership_price(
                "institution_yearly"
            )

    }

    return render_template(

        "membership.html",

        plans=plans,

        app=APP_INFO

    )


# ==========================================================
# ABOUT
# ==========================================================

@app.route("/about")
def about():

    return render_template(

        "about.html",

        app=APP_INFO

    )
