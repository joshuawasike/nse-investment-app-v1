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
