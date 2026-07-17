"""
Energy Inflation Correlation Engine — Interactive Dashboard
--------------------------------------------------------------
Streamlit app: live-fetches WTI oil + CPI data from FRED, lets the user
explore time-lagged correlation interactively.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_datareader import data as web
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
SERIES = {
    "oil": "MCOILWTICO",
    "cpi_headline": "CPIAUCSL",
    "cpi_core": "CPILFESL",
    "cpi_gasoline": "CUSR0000SETB01",
}
LABELS = {
    "cpi_headline": "Headline CPI",
    "cpi_core": "Core CPI (ex food & energy)",
    "cpi_gasoline": "Gasoline CPI",
}

st.set_page_config(page_title="Energy Inflation Correlation Engine", layout="wide")


# ---------------------------------------------------------------------------
# DATA FETCH — cached so the app doesn't hit FRED on every widget interaction.
# ttl=3600 means it will re-fetch fresh data at most once per hour, which is
# the "live-refreshing" part: whenever the cache expires, the next load pulls
# whatever FRED has published since, including a same-day new gasoline print.
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Fetching latest data from FRED...")
def fetch_fred_series(start: str):
    frames = {}
    for label, code in SERIES.items():
        s = web.DataReader(code, "fred", start, None)[code]
        frames[label] = s
    df = pd.DataFrame(frames)
    df.index = pd.to_datetime(df.index)
    df = df.resample("MS").mean()
    return df.dropna(how="all")


def to_pct_change(df, kind):
    if kind == "MoM (month-over-month)":
        return df.pct_change().dropna(how="all")
    return df.pct_change(periods=12).dropna(how="all")


def lagged_regression(oil_change, cpi_change, max_lag):
    rows = []
    for lag in range(0, max_lag + 1):
        oil_lagged = oil_change.shift(lag)
        combined = pd.concat([oil_lagged, cpi_change], axis=1).dropna()
        combined.columns = ["oil", "cpi"]
        if len(combined) < 10:
            continue
        X = sm.add_constant(combined["oil"])
        model = sm.OLS(combined["cpi"], X).fit()
        rows.append({
            "lag_months": lag,
            "pearson_r": combined["oil"].corr(combined["cpi"]),
            "r_squared": model.rsquared,
            "beta": model.params["oil"],
            "p_value": model.pvalues["oil"],
            "n_obs": len(combined),
        })
    return pd.DataFrame(rows)


def stationarity_check(series, name):
    """Augmented Dickey-Fuller test. Granger requires stationary series;
    % change series usually pass, levels usually don't."""
    result = adfuller(series.dropna(), autolag="AIC")
    return {
        "series": name,
        "adf_statistic": result[0],
        "p_value": result[1],
        "stationary_at_5pct": result[1] < 0.05,
    }


def granger_test(cause, effect, max_lag):
    """Granger causality: does adding lagged `cause` improve prediction of
    `effect` beyond effect's own lags? Returns p-value per lag (ssr F-test)."""
    combined = pd.concat([effect, cause], axis=1).dropna()
    combined.columns = ["effect", "cause"]
    if len(combined) < max_lag + 20:
        return None
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):  # silence verbose printout
        out = grangercausalitytests(combined[["effect", "cause"]], maxlag=max_lag)
    rows = []
    for lag, res in out.items():
        f_test = res[0]["ssr_ftest"]
        rows.append({
            "lag_months": lag,
            "F_statistic": f_test[0],
            "p_value": f_test[1],
            "significant_at_5pct": f_test[1] < 0.05,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------------------------
st.sidebar.header("Controls")

start_date = st.sidebar.date_input("Data start date", value=datetime(2000, 1, 1))
change_type = st.sidebar.radio(
    "Change type",
    ["YoY (year-over-year)", "MoM (month-over-month)"],
    help="YoY is smoother but its 'best lag' is distorted by autocorrelation "
         "(each YoY value shares 11 months with its neighbor). MoM is noisier "
         "but gives a more defensible lag estimate.",
)
max_lag = st.sidebar.slider("Max lag to test (months)", 3, 24, 12)
cpi_choice = st.sidebar.selectbox(
    "CPI series to correlate against oil",
    options=list(LABELS.keys()),
    format_func=lambda k: LABELS[k],
)

if st.sidebar.button("Force refresh from FRED"):
    st.cache_data.clear()

st.sidebar.caption(
    "Data source: FRED (Federal Reserve Economic Data). "
    "Cache refreshes hourly, or click 'Force refresh' for the latest pull."
)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
st.title("⛽ Energy Inflation Correlation Engine")
st.markdown(
    "Measures how oil price shocks pass through into U.S. consumer inflation, "
    "using time-lagged linear regression against live FRED data."
)

raw = fetch_fred_series(start_date.isoformat())
st.caption(
    f"Loaded {len(raw)} monthly observations, "
    f"{raw.index.min().date()} to {raw.index.max().date()} "
    f"(last FRED data point available as of this fetch)."
)

changes = to_pct_change(raw, change_type)

# --- Run regression for ALL three CPI series, so the comparison chart always
#     shows all three, while the selected one gets the spotlight ---
all_results = {}
for key in LABELS:
    all_results[key] = lagged_regression(changes["oil"], changes[key], max_lag)

selected_res = all_results[cpi_choice]
best_row = selected_res.loc[selected_res["r_squared"].idxmax()]

# --- Headline metrics ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Best lag", f"{int(best_row['lag_months'])} months")
c2.metric("R-squared at best lag", f"{best_row['r_squared']:.3f}")
c3.metric("Pearson r at best lag", f"{best_row['pearson_r']:.3f}")
c4.metric("p-value", f"{best_row['p_value']:.4f}")

st.divider()

# --- Chart 1: lag vs R-squared, all three series, interactive ---
st.subheader("Explanatory power (R²) by lag, across all CPI measures")
fig1 = go.Figure()
for key, res in all_results.items():
    fig1.add_trace(go.Scatter(
        x=res["lag_months"], y=res["r_squared"],
        mode="lines+markers", name=LABELS[key],
        line=dict(width=3 if key == cpi_choice else 1.5),
    ))
fig1.update_layout(
    xaxis_title="Lag (months, oil leads CPI)",
    yaxis_title="R-squared",
    hovermode="x unified",
    height=450,
)
st.plotly_chart(fig1, use_container_width=True)

# --- Chart 2: oil vs selected CPI, dual axis so CPI isn't crushed by scale ---
st.subheader(f"WTI Oil vs. {LABELS[cpi_choice]} — dual axis")
fig2 = make_subplots(specs=[[{"secondary_y": True}]])
fig2.add_trace(
    go.Scatter(x=changes.index, y=changes["oil"] * 100, name="WTI Oil (%)", line=dict(color="black")),
    secondary_y=False,
)
fig2.add_trace(
    go.Scatter(x=changes.index, y=changes[cpi_choice] * 100, name=f"{LABELS[cpi_choice]} (%)", line=dict(color="crimson")),
    secondary_y=True,
)
fig2.update_yaxes(title_text="Oil % change", secondary_y=False)
fig2.update_yaxes(title_text=f"{LABELS[cpi_choice]} % change", secondary_y=True)
fig2.update_layout(hovermode="x unified", height=450)
st.plotly_chart(fig2, use_container_width=True)

# --- Data table + download ---
st.subheader(f"Full regression results — {LABELS[cpi_choice]}")
st.dataframe(selected_res.style.format({
    "pearson_r": "{:.4f}", "r_squared": "{:.4f}", "beta": "{:.4f}", "p_value": "{:.4f}",
}), use_container_width=True)

st.download_button(
    "Download results as CSV",
    selected_res.to_csv(index=False),
    file_name=f"results_{cpi_choice}_{change_type.split()[0].lower()}.csv",
)

st.divider()

# ---------------------------------------------------------------------------
# GRANGER CAUSALITY — goes beyond correlation: does oil *predictively cause*
# CPI in the Granger sense (lagged oil improves CPI forecasts beyond CPI's
# own history)? Also tests the reverse direction as a sanity check.
# ---------------------------------------------------------------------------
st.subheader("Granger causality: beyond correlation")
st.markdown(
    "Correlation can't distinguish *oil drives CPI* from *both react to something else*. "
    "The Granger test asks a sharper question: **do past oil changes improve prediction of "
    "CPI changes, beyond what CPI's own past already predicts?** "
    "It also runs the reverse direction (CPI → oil) as a falsification check — "
    "if that were also 'significant', it would suggest a common driver rather than causation."
)

granger_lag = st.slider("Granger test: max lag (months)", 1, 12, 6, key="granger_lag")

# Stationarity check first — Granger is invalid on non-stationary series
stat_rows = [
    stationarity_check(changes["oil"], "Oil (% change)"),
    stationarity_check(changes[cpi_choice], f"{LABELS[cpi_choice]} (% change)"),
]
stat_df = pd.DataFrame(stat_rows)
both_stationary = stat_df["stationary_at_5pct"].all()

with st.expander("Stationarity check (ADF test) — precondition for Granger"):
    st.dataframe(stat_df.style.format({"adf_statistic": "{:.3f}", "p_value": "{:.4f}"}),
                 use_container_width=True)
    if both_stationary:
        st.success("Both series are stationary at the 5% level — Granger results below are valid.")
    else:
        st.warning(
            "At least one series is NOT stationary — Granger p-values below may be unreliable. "
            "This is common with YoY changes (smooth, autocorrelated); try switching to MoM."
        )

col_fwd, col_rev = st.columns(2)

with col_fwd:
    st.markdown(f"**Oil → {LABELS[cpi_choice]}** (the hypothesis)")
    g_fwd = granger_test(changes["oil"], changes[cpi_choice], granger_lag)
    if g_fwd is not None:
        st.dataframe(g_fwd.style.format({"F_statistic": "{:.2f}", "p_value": "{:.4f}"}),
                     use_container_width=True)
        n_sig = int(g_fwd["significant_at_5pct"].sum())
        if n_sig > 0:
            st.success(f"Oil Granger-causes {LABELS[cpi_choice]} at {n_sig}/{len(g_fwd)} tested lags (p < 0.05).")
        else:
            st.info("No significant Granger causality found at tested lags.")
    else:
        st.info("Not enough observations for this lag depth.")

with col_rev:
    st.markdown(f"**{LABELS[cpi_choice]} → Oil** (falsification check)")
    g_rev = granger_test(changes[cpi_choice], changes["oil"], granger_lag)
    if g_rev is not None:
        st.dataframe(g_rev.style.format({"F_statistic": "{:.2f}", "p_value": "{:.4f}"}),
                     use_container_width=True)
        n_sig_rev = int(g_rev["significant_at_5pct"].sum())
        if n_sig_rev == 0:
            st.success("No reverse causality — consistent with oil being the driver.")
        else:
            st.warning(
                f"Reverse direction also 'significant' at {n_sig_rev}/{len(g_rev)} lags. "
                "This can indicate feedback (inflation expectations affecting oil demand) "
                "or a common driver (e.g. global growth) — worth noting in any write-up."
            )
    else:
        st.info("Not enough observations for this lag depth.")

with st.expander("Methodology & limitations"):
    st.markdown("""
- **% change, not levels**: regressing raw price levels on raw CPI levels gives spurious
  correlation because both series trend upward over time. Converting to % change removes that.
- **YoY vs MoM**: YoY series are smooth because each observation shares 11 months of data
  with its neighbor — this artificially stretches out the "best lag." MoM is noisier but
  a more honest estimate of true transmission speed.
- **Correlation vs. Granger causality**: the lag regression shows predictive association.
  The Granger section goes one step further — testing whether lagged oil improves CPI
  forecasts beyond CPI's own history, in both directions. Note that even Granger causality
  is *predictive* causality, not structural/economic causality; a full structural claim
  would need a VAR/SVAR model with identification assumptions.
- **Stationarity**: Granger tests require stationary inputs. The dashboard runs an ADF
  test first and warns you if the precondition fails (common for smooth YoY series).
- **Data cadence**: WTI oil updates daily on FRED; CPI updates once a month (mid-month,
  for the prior month). "Live" here means the dashboard re-fetches on each cache refresh,
  not that the underlying data itself updates in real time.
""")
