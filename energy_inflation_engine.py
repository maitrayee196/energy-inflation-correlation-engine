"""
Energy Inflation Correlation Engine
------------------------------------
Measures how oil price shocks propagate into consumer inflation, using
time-lagged linear regressions between crude oil prices and CPI.

Data source : FRED (Federal Reserve Economic Data), via pandas_datareader
Tech stack  : pandas, statsmodels, matplotlib

Run:
    pip install pandas pandas_datareader statsmodels matplotlib
    python energy_inflation_engine.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from pandas_datareader import data as web

# ---------------------------------------------------------------------------
# 1. CONFIG
# ---------------------------------------------------------------------------
START = "2000-01-01"
END = None  # None = through latest available

SERIES = {
    "oil": "MCOILWTICO",       # WTI crude, monthly average, $/bbl
    "cpi_headline": "CPIAUCSL",  # CPI, all urban consumers, SA
    "cpi_core": "CPILFESL",      # Core CPI (ex food & energy)
    "cpi_gasoline": "CUSR0000SETB01",  # CPI: gasoline component
}

MAX_LAG_MONTHS = 12          # how many months of lag to test
CHANGE_TYPE = "yoy"          # "mom" (month-over-month) or "yoy" (year-over-year)


# ---------------------------------------------------------------------------
# 2. FETCH DATA FROM FRED
# ---------------------------------------------------------------------------
def fetch_fred_series(series_dict, start, end):
    frames = {}
    for label, code in series_dict.items():
        s = web.DataReader(code, "fred", start, end)[code]
        frames[label] = s
    df = pd.DataFrame(frames)
    df.index = pd.to_datetime(df.index)
    df = df.resample("MS").mean()  # ensure monthly, month-start aligned
    return df


# ---------------------------------------------------------------------------
# 3. TRANSFORM: % CHANGE (avoids spurious correlation from shared trends)
# ---------------------------------------------------------------------------
def to_pct_change(df, kind="yoy"):
    if kind == "mom":
        return df.pct_change().dropna(how="all")
    elif kind == "yoy":
        return df.pct_change(periods=12).dropna(how="all")
    else:
        raise ValueError("kind must be 'mom' or 'yoy'")


# ---------------------------------------------------------------------------
# 4. TIME-LAGGED REGRESSION: for each lag, regress CPI change on
#    oil change from `lag` months earlier
# ---------------------------------------------------------------------------
def lagged_regression(oil_change, cpi_change, max_lag):
    results = []
    for lag in range(0, max_lag + 1):
        oil_lagged = oil_change.shift(lag)
        combined = pd.concat([oil_lagged, cpi_change], axis=1).dropna()
        combined.columns = ["oil", "cpi"]
        if len(combined) < 10:
            continue

        X = sm.add_constant(combined["oil"])
        y = combined["cpi"]
        model = sm.OLS(y, X).fit()

        pearson_r = combined["oil"].corr(combined["cpi"])

        results.append({
            "lag_months": lag,
            "pearson_r": round(pearson_r, 4),
            "r_squared": round(model.rsquared, 4),
            "beta": round(model.params["oil"], 4),
            "p_value": round(model.pvalues["oil"], 4),
            "n_obs": len(combined),
        })
    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------------------
def main():
    print("Fetching FRED series...")
    raw = fetch_fred_series(SERIES, START, END)
    raw = raw.dropna(how="all")
    print(f"Pulled {len(raw)} monthly observations from {raw.index.min().date()} "
          f"to {raw.index.max().date()}")

    changes = to_pct_change(raw, kind=CHANGE_TYPE)

    cpi_targets = ["cpi_headline", "cpi_core", "cpi_gasoline"]
    all_results = {}

    for target in cpi_targets:
        print(f"\n=== Oil -> {target} ({CHANGE_TYPE} change, lags 0-{MAX_LAG_MONTHS}mo) ===")
        res = lagged_regression(changes["oil"], changes[target], MAX_LAG_MONTHS)
        print(res.to_string(index=False))
        all_results[target] = res

        best = res.loc[res["r_squared"].idxmax()]
        print(f"-> Strongest fit at lag = {int(best['lag_months'])} months "
              f"(R^2 = {best['r_squared']}, r = {best['pearson_r']})")

    # Save results to CSV
    combined_out = pd.concat(
        {k: v.set_index("lag_months") for k, v in all_results.items()}, axis=1
    )
    combined_out.to_csv("energy_inflation_results.csv")
    print("\nSaved lagged regression results -> energy_inflation_results.csv")

    # -----------------------------------------------------------------
    # Plot 1: R-squared vs lag, for each CPI series
    # -----------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    for target, res in all_results.items():
        ax.plot(res["lag_months"], res["r_squared"], marker="o", label=target)
    ax.set_xlabel("Lag (months, oil leads CPI)")
    ax.set_ylabel("R-squared")
    ax.set_title(f"Oil Price -> CPI: Explanatory Power by Lag ({CHANGE_TYPE.upper()} change)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("lag_vs_rsquared.png", dpi=150)
    print("Saved chart -> lag_vs_rsquared.png")

    # -----------------------------------------------------------------
    # Plot 2: Oil vs headline CPI, overlaid, % change
    # -----------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(11, 5))
    ax2.plot(changes.index, changes["oil"] * 100, label="WTI Oil (% chg)", color="black")
    ax2.plot(changes.index, changes["cpi_headline"] * 100, label="Headline CPI (% chg)", color="crimson")
    ax2.set_ylabel(f"{CHANGE_TYPE.upper()} % change")
    ax2.set_title("WTI Crude Oil vs. Headline CPI")
    ax2.legend()
    ax2.grid(alpha=0.3)
    fig2.tight_layout()
    fig2.savefig("oil_vs_cpi_overlay.png", dpi=150)
    print("Saved chart -> oil_vs_cpi_overlay.png")


if __name__ == "__main__":
    main()
