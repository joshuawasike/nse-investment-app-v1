"""
==========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Company Research Engine
==========================================================
"""

import json
import os


# ==========================================================
# Locate data folder
# ==========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")

COMPANY_FILE = os.path.join(DATA_DIR, "companies.json")


# ==========================================================
# Load Company Database
# ==========================================================

def load_companies():

    if not os.path.exists(COMPANY_FILE):
        return []

    with open(COMPANY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================================================
# Get All Companies
# ==========================================================

def all_companies():

    return load_companies()


# ==========================================================
# Find Company by Code
# ==========================================================

def get_company(code):

    companies = load_companies()

    for company in companies:

        if company["code"].upper() == code.upper():
            return company

    return None


# ==========================================================
# Search Companies
# ==========================================================

def search_company(keyword):

    keyword = keyword.lower()

    companies = load_companies()

    results = []

    for company in companies:

        if (
            keyword in company["name"].lower()
            or keyword in company["code"].lower()
            or keyword in company["sector"].lower()
            or keyword in company["industry"].lower()
        ):
            results.append(company)

    return results


# ==========================================================
# Companies by Sector
# ==========================================================

def companies_by_sector(sector):

    companies = load_companies()

    return [
        c for c in companies
        if c["sector"].lower() == sector.lower()
    ]


# ==========================================================
# Highest Dividend Companies
# ==========================================================

def top_dividend(limit=10):

    companies = load_companies()

    return sorted(
        companies,
        key=lambda x: x["dividend_yield"],
        reverse=True
    )[:limit]


# ==========================================================
# Highest Quality Companies
# ==========================================================

def top_quality(limit=10):

    companies = load_companies()

    return sorted(
        companies,
        key=lambda x: x["quality_score"],
        reverse=True
    )[:limit]


# ==========================================================
# Highest ROE
# ==========================================================

def top_roe(limit=10):

    companies = load_companies()

    return sorted(
        companies,
        key=lambda x: x["roe"],
        reverse=True
    )[:limit]


# ==========================================================
# Largest Companies
# ==========================================================

def largest_companies(limit=10):

    companies = load_companies()

    return sorted(
        companies,
        key=lambda x: x["market_cap"],
        reverse=True
    )[:limit]


# ==========================================================
# Lowest PE Ratio
# ==========================================================

def value_companies(limit=10):

    companies = load_companies()

    companies = [
        c for c in companies
        if c["pe_ratio"] > 0
    ]

    return sorted(
        companies,
        key=lambda x: x["pe_ratio"]
    )[:limit]


# ==========================================================
# Best ESG Companies
# ==========================================================

def best_esg():

    companies = load_companies()

    return sorted(
        companies,
        key=lambda x: x["health_score"],
        reverse=True
    )


# ==========================================================
# Company Statistics
# ==========================================================

def statistics():

    companies = load_companies()

    if not companies:

        return {}

    total_market_cap = sum(
        c["market_cap"]
        for c in companies
    )

    avg_dividend = sum(
        c["dividend_yield"]
        for c in companies
    ) / len(companies)

    avg_roe = sum(
        c["roe"]
        for c in companies
    ) / len(companies)

    avg_pe = sum(
        c["pe_ratio"]
        for c in companies
    ) / len(companies)

    avg_health = sum(
        c["health_score"]
        for c in companies
    ) / len(companies)

    return {

        "companies": len(companies),

        "market_cap": total_market_cap,

        "average_dividend": round(avg_dividend, 2),

        "average_roe": round(avg_roe, 2),

        "average_pe": round(avg_pe, 2),

        "average_health": round(avg_health, 2)

    }


# ==========================================================
# Research Dashboard
# ==========================================================

def dashboard():

    return {

        "statistics": statistics(),

        "top_dividend": top_dividend(5),

        "top_quality": top_quality(5),

        "top_roe": top_roe(5),

        "largest": largest_companies(5),

        "value": value_companies(5)

    }
