# =========================================================
# JOBURA WEALTH®
# CORPORATE ACTION ENGINE
# =========================================================

import numpy as np

# =========================================================
# CORPORATE ACTION DATABASE
# =========================================================

CORPORATE_ACTIONS = {

    # Paste the entire CORPORATE_ACTIONS dictionary here

}

# =========================================================
# APPLY CORPORATE ACTIONS
# =========================================================

def apply_corporate_actions(capital, code):
    """
    Simulates corporate actions for a company.

    Parameters
    ----------
    capital : float
        Current investment value.

    code : str
        NSE stock code.

    Returns
    -------
    tuple
        (updated_capital, bonus_dividend)
    """

    profile = CORPORATE_ACTIONS.get(code)

    if profile is None:
        return capital, 0.0

    bonus = 0.0

    # -----------------------------------------------------
    # Bonus Shares
    # -----------------------------------------------------
    if np.random.rand() < profile["bonus"]:
        capital *= 1.10

    # -----------------------------------------------------
    # Rights Issue
    # -----------------------------------------------------
    if np.random.rand() < profile["rights"]:
        capital *= 1.05

    # -----------------------------------------------------
    # Share Buyback
    # -----------------------------------------------------
    if np.random.rand() < profile["buyback"]:
        capital *= 1.03

    # -----------------------------------------------------
    # Stock Split
    # -----------------------------------------------------
    if np.random.rand() < profile["split"]:
        capital *= 1.00

    # -----------------------------------------------------
    # Special Dividend
    # -----------------------------------------------------
    if np.random.rand() < profile["special_dividend"]:
        bonus = capital * 0.03

    return capital, bonus
