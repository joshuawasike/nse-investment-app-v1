# =========================================================
# JOBURA WEALTH®
# Portfolio Construction Engine
# =========================================================

from engine.analytics import company_analytics


# =========================================================
# BUILD PORTFOLIO
# =========================================================
def build_portfolio(
    assets,
    weights,
    capital,
    dividends,
    invested,
    annual_return,
):
    """
    Builds the institutional portfolio breakdown
    used by the simulation engine.
    """

    breakdown = []

    asset_values = capital + dividends

    for i, asset in enumerate(assets):

        code = asset[1]

        analytics = company_analytics(
            code,
            capital[i]
        )

        invested_asset = invested * weights[i]

        breakdown.append({

            # ----------------------------------
            # Identity
            # ----------------------------------
            "asset": asset[0],
            "code": code,

            # ----------------------------------
            # Allocation
            # ----------------------------------
            "allocation_pct": round(weights[i] * 100, 2),

            # ----------------------------------
            # Investment
            # ----------------------------------
            "capital": round(float(invested_asset), 2),

            "current_value": round(float(capital[i]), 2),

            "capital_gain": round(
                float(capital[i] - invested_asset),
                2
            ),

            # ----------------------------------
            # Income
            # ----------------------------------
            "dividends": round(
                float(dividends[i]),
                2
            ),

            "total_return": round(
                float(asset_values[i]),
                2
            ),

            # ----------------------------------
            # Analytics
            # ----------------------------------
            "dividend_yield": analytics["yield"],

            "dividend_growth": analytics["growth"],

            "dividend_health": analytics["health"],

            "quality_score": analytics["quality"],

            "stability_score": analytics["stability"],

            "estimated_income": analytics["income"],

            "beta": analytics["beta"],

            "policy": analytics["policy"],

            "sector": analytics["sector"],

            "roe": analytics["roe"],

            "pe": analytics["pe"],

            "pb": analytics["pb"],

            "credit": analytics["credit"],

            "esg": analytics["esg"],

            "annual_return": round(
                annual_return * 100,
                2
            )

        })

    return breakdown
# =========================================================
# BUILD MONTHLY INVESTMENT PLAN
# =========================================================

def build_investment_plan(
    assets,
    weights,
    monthly
):
    """
    Creates the monthly investment allocation plan.
    """

    plan = []

    allocation = monthly * weights

    for i, asset in enumerate(assets):

        plan.append({

            "name": asset[0],

            "code": asset[1],

            "allocation_pct": round(
                weights[i] * 100,
                2
            ),

            "monthly_amount": round(
                float(allocation[i]),
                2
            )

        })

    return plan
# =========================================================
# BUILD RETURNS TABLE
# =========================================================

def build_returns_table(portfolio):
    """
    Builds the institutional performance table.
    """

    table = []

    for asset in portfolio:

        table.append({

            "asset": asset["asset"],

            "code": asset["code"],

            "allocation": asset["allocation_pct"],

            "capital": asset["capital"],

            "current_value": asset["current_value"],

            "capital_gain": asset["capital_gain"],

            "dividends": asset["dividends"],

            "total_return": asset["total_return"],

            "annual_return": asset["annual_return"]

        })

    return table
