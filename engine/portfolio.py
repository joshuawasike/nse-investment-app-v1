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
