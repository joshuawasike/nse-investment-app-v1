"""
==========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Utility Functions
==========================================================
"""

import json
import os
import random
from datetime import datetime


# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")


# ==========================================================
# JSON HELPERS
# ==========================================================

def load_json(filename):

    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):

    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ==========================================================
# CURRENCY
# ==========================================================

def money(value):

    return f"KES {value:,.2f}"


# ==========================================================
# PERCENTAGE
# ==========================================================

def percent(value):

    return f"{value:.2f}%"


# ==========================================================
# DATE
# ==========================================================

def today():

    return datetime.now().strftime("%d %B %Y")


def timestamp():

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==========================================================
# RANDOM MARKET MOVEMENT
# ==========================================================

def random_growth():

    return round(random.uniform(8, 25), 2)


def random_dividend():

    return round(random.uniform(3, 10), 2)


def random_risk():

    return round(random.uniform(15, 75), 2)


# ==========================================================
# MARKET REGIME
# ==========================================================

def market_regime():

    return random.choice(

        [

            "Bull",

            "Normal",

            "Bear"

        ]

    )


# ==========================================================
# HEALTH SCORE
# ==========================================================

def health_colour(score):

    if score >= 90:
        return "Excellent"

    elif score >= 75:
        return "Very Good"

    elif score >= 60:
        return "Good"

    elif score >= 40:
        return "Moderate"

    return "Poor"


# ==========================================================
# RISK COLOUR
# ==========================================================

def risk_colour(level):

    level = str(level).upper()

    if level == "LOW":
        return "#22c55e"

    if level == "MEDIUM":
        return "#f59e0b"

    return "#ef4444"


# ==========================================================
# COMPANY LOOKUP
# ==========================================================

def company_name(code):

    companies = load_json("companies.json")

    for company in companies:

        if company["code"] == code:
            return company["name"]

    return code


# ==========================================================
# TOP COMPANIES
# ==========================================================

def top_companies(limit=5):

    companies = load_json("companies.json")

    companies = sorted(

        companies,

        key=lambda x: x["quality_score"],

        reverse=True

    )

    return companies[:limit]


# ==========================================================
# USER LOOKUP
# ==========================================================

def find_user(transaction_code):

    users = load_json("users.json")

    for user in users:

        if user.get("code") == transaction_code:
            return user

    return None


# ==========================================================
# SUBSCRIPTION CHECK
# ==========================================================

def is_premium(user):

    if not user:
        return False

    status = user.get("status", "").lower()

    return (

        "monthly" in status

        or

        "yearly" in status

    )


# ==========================================================
# PLATFORM INFORMATION
# ==========================================================

def platform():

    return {

        "name":

            "JOBURA WEALTH®",

        "system":

            "NSE Institutional Wealth Management Platform",

        "edition":

            "Professional Analytics Suite",

        "version":

            "2026",

        "company":

            "Jobura Solutions"

    }


# ==========================================================
# DASHBOARD KPI
# ==========================================================

def kpi(summary):

    return {

        "invested":

            money(summary["invested"]),

        "value":

            money(summary["value"]),

        "profit":

            money(summary["profit"]),

        "roi":

            percent(summary["roi"]),

        "dividends":

            money(summary["dividends"])

    }


# ==========================================================
# APPLICATION FOOTER
# ==========================================================

def footer():

    return (

        "© 2026 JOBURA WEALTH® | "

        "NSE Institutional Wealth Management Platform | "

        "Professional Analytics Suite"

    )
