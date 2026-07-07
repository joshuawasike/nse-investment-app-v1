"""
==========================================================
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Retirement Planning Engine
==========================================================
"""

import math


# ==========================================================
# Future Value of Monthly Investments
# ==========================================================

def future_value(monthly, years, annual_return=12):

    """
    Calculates future value of monthly investments.
    """

    monthly_rate = annual_return / 100 / 12

    months = years * 12

    if monthly_rate == 0:
        return monthly * months

    fv = monthly * (
        ((1 + monthly_rate) ** months - 1)
        / monthly_rate
    )

    return round(fv, 2)


# ==========================================================
# Required Monthly Contribution
# ==========================================================

def required_monthly(target, years, annual_return=12):

    monthly_rate = annual_return / 100 / 12

    months = years * 12

    if monthly_rate == 0:
        return round(target / months, 2)

    payment = target * monthly_rate

    payment /= (
        ((1 + monthly_rate) ** months) - 1
    )

    return round(payment, 2)


# ==========================================================
# Safe Withdrawal (4% Rule)
# ==========================================================

def safe_monthly_income(portfolio_value):

    annual_income = portfolio_value * 0.04

    return round(annual_income / 12, 2)


# ==========================================================
# Years Portfolio Can Sustain Retirement
# ==========================================================

def sustainability_years(
        portfolio,
        annual_expenses,
        annual_return=8):

    if annual_expenses <= 0:
        return 0

    years = 0

    balance = portfolio

    while balance > 0 and years < 100:

        growth = balance * annual_return / 100

        balance += growth

        balance -= annual_expenses

        years += 1

    return years


# ==========================================================
# Retirement Readiness
# ==========================================================

def readiness(score):

    if score >= 90:
        return "Excellent"

    elif score >= 75:
        return "Very Good"

    elif score >= 60:
        return "Moderate"

    elif score >= 40:
        return "Needs Improvement"

    return "High Risk"


# ==========================================================
# Retirement Score
# ==========================================================

def retirement_score(
        portfolio,
        target):

    if target <= 0:
        return 0

    score = (portfolio / target) * 100

    score = max(0, min(score, 100))

    return round(score, 2)


# ==========================================================
# Retirement Projection
# ==========================================================

def projection(
        monthly,
        years,
        target,
        annual_return=12):

    portfolio = future_value(
        monthly,
        years,
        annual_return
    )

    score = retirement_score(
        portfolio,
        target
    )

    monthly_income = safe_monthly_income(
        portfolio
    )

    report = {

        "portfolio": portfolio,

        "target": target,

        "achievement": score,

        "status": readiness(score),

        "monthly_income": monthly_income,

        "required_monthly":
            required_monthly(
                target,
                years,
                annual_return
            )

    }

    return report


# ==========================================================
# Retirement Timeline
# ==========================================================

def timeline(
        monthly,
        years,
        annual_return=12):

    data = []

    for year in range(1, years + 1):

        value = future_value(
            monthly,
            year,
            annual_return
        )

        data.append({

            "year": year,

            "portfolio": value

        })

    return data
