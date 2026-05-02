import os
from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import glob
import matplotlib

# =========================
# SAFE BACKEND (RENDER FIX)
# =========================
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# =========================
# SAFE DATA LOADING
# =========================
def load_data():
    df = pd.DataFrame(columns=["Code", "Date", "Previous"])

    try:
        files = glob.glob("data/nse_csv/*.csv")
    except:
        files = []

    if not files:
        return df

    for file in files:
        try:
            temp = pd.read_csv(file, usecols=["Code", "Date", "Previous"])
            df = pd.concat([df, temp], ignore_index=True)
        except:
            continue

    if not df.empty:
        try:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df["Previous"] = pd.to_numeric(df["Previous"], errors="coerce")
            df = df.dropna()
            df = df.sort_values(["Code", "Date"])
        except:
            pass

    return df


df = load_data()

# =========================
# ASSETS
# =========================
ASSETS = [
    ("Equity Bank", "EQTY", 0.055),
    ("KCB Group", "KCB", 0.065),
    ("Co-op Bank", "COOP", 0.075),
    ("Safaricom", "SCOM", 0.060),
    ("EABL", "EABL", 0.050),
    ("KenGen", "KEGN", 0.040),
    ("NCBA", "NCBA", 0.035),
    ("Kenya Airways", "KQ", 0.000),
]

N = len(ASSETS)

# =========================
# SAFE RETURNS
# =========================
def get_returns():

    R = []

    for _, code, _ in ASSETS:

        try:
            px = df[df["Code"] == code]["Previous"].values
        except:
            px = []

        px = np.nan_to_num(px)

        if len(px) < 40:
            r = np.random.normal(0.0005, 0.01, 220)
        else:
            r = np.diff(np.log(px + 1e-9))

        r = np.nan_to_num(r)
        r = np.clip(r, -0.03, 0.03)

        if len(r) < 220:
            r = np.pad(r, (0, 220 - len(r)), mode="wrap")
        else:
            r = r[:220]

        R.append(r)

    return np.array(R)

# =========================
# SIMULATION (SAFE)
# =========================
def simulate(monthly, years):

    R = get_returns()

    months = max(int(years * 12), 1)
    base = monthly * months

    capital = 0.0
    curve = []

    for t in range(months):

        r = R[:, np.random.randint(0, 220)]
        portfolio_return = np.mean(r)

        capital += monthly
        capital *= (1 + portfolio_return)

        if not np.isfinite(capital):
            capital = base

        curve.append(capital)

    return {
        "invested": base,
        "value": curve[-1],
        "curve": curve
    }

# =========================
# CHART
# =========================
def chart(curve):

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    ax.plot(curve, color="#60a5fa", linewidth=2)
    ax.set_title("Institutional Alpha Terminal", color="white")

    ax.tick_params(colors="white")
    for s in ax.spines.values():
        s.set_color("white")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    img = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return img

# =========================
# ROUTE
# =========================
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        monthly = float(request.form.get("monthly", 0))
        years = int(request.form.get("years", 1))

        result = simulate(monthly, years)

        return render_template(
            "index.html",
            data=result,
            chart=chart(result["curve"])
        )

    return render_template("index.html", data=None)

# =========================
# RENDER ENTRY POINT FIX
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
