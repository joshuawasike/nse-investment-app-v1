"""
==========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Institutional Reporting Engine
==========================================================
"""

from datetime import datetime


# ==========================================================
# Currency Formatting
# ==========================================================

def money(value):

    return f"KES {value:,.2f}"


# ==========================================================
# Percentage Formatting
# ==========================================================

def pct(value):

    return f"{value:.2f}%"


# ==========================================================
# Executive Summary
# ==========================================================

def executive_summary(summary):

    return {

        "Capital Invested":
            money(summary["invested"]),

        "Portfolio Value":
            money(summary["value"]),

        "Capital Gain":
            money(summary["profit"]),

        "Dividend Income":
            money(summary["dividends"]),

        "Total Return":
            money(summary["total_return"]),

        "ROI":
            pct(summary["roi"])

    }


# ==========================================================
# Portfolio Allocation
# ==========================================================

def allocation(plan):

    rows = []

    for asset in plan:

        rows.append({

            "Company":
                asset["name"],

            "Allocation":
                pct(asset["percent"]),

            "Investment":
                money(asset["kes"])

        })

    return rows


# ==========================================================
# Company Performance
# ==========================================================

def performance(returns):

    rows = []

    for company in returns:

        rows.append({

            "Company":
                company["name"],

            "Value":
                money(company["value"]),

            "Dividends":
                money(company["dividends"]),

            "ROI":
                pct(company["roi"]),

            "Risk":
                company["risk_level"]

        })

    return rows


# ==========================================================
# Risk Report
# ==========================================================

def risk_section(risk):

    return {

        "Portfolio Risk":
            risk["classification"],

        "Risk Score":
            risk["risk_score"],

        "Volatility":
            pct(risk["volatility"]),

        "Sharpe Ratio":
            risk["sharpe_ratio"],

        "Sortino Ratio":
            risk["sortino_ratio"],

        "Maximum Drawdown":
            pct(risk["max_drawdown"]),

        "Value at Risk":
            pct(risk["value_at_risk"])

    }


# ==========================================================
# AI Recommendation
# ==========================================================

def ai_section(ai):

    return {

        "Portfolio Health":
            ai["health"],

        "Institutional Rating":
            ai["rating"],

        "Diversification":
            ai["diversification"],

        "Dividend Score":
            ai["dividend_score"],

        "Risk":
            ai["risk"],

        "AI Commentary":
            ai["message"]

    }


# ==========================================================
# Retirement Report
# ==========================================================

def retirement_section(retirement):

    return {

        "Target":
            money(retirement["target"]),

        "Projected Portfolio":
            money(retirement["portfolio"]),

        "Achievement":
            pct(retirement["achievement"]),

        "Status":
            retirement["status"],

        "Monthly Retirement Income":
            money(retirement["monthly_income"]),

        "Required Monthly Saving":
            money(retirement["required_monthly"])

    }


# ==========================================================
# Complete Institutional Report
# ==========================================================

def generate_report(

        summary,

        plan,

        returns,

        risk,

        ai,

        retirement,

        model,

        scenario

):

    return {

        "platform":

            "JOBURA WEALTH®",

        "system":

            "NSE Institutional Wealth Management Platform",

        "generated":

            datetime.now().strftime(
                "%d %B %Y %H:%M"
            ),

        "scenario":

            scenario.upper(),

        "model":

            model.upper(),

        "executive_summary":

            executive_summary(summary),

        "allocation":

            allocation(plan),

        "performance":

            performance(returns),

        "risk":

            risk_section(risk),

        "ai":

            ai_section(ai),

        "retirement":

            retirement_section(retirement)

    }


# ==========================================================
# Printable Cover Page
# ==========================================================

def cover():

    return {

        "title":
            "JOBURA WEALTH®",

        "subtitle":
            "NSE Institutional Wealth Management Platform",

        "edition":
            "Professional Analytics Suite",

        "version":
            "Version 2026",

        "copyright":
            "© 2026 Jobura Solutions. All Rights Reserved."

    }
