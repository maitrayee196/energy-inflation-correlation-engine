# Energy Inflation Correlation Engine

**When oil prices jump, how long does it take before you feel it at the store — and how much of inflation is really just oil?**

This project answers that question with real data. It pulls crude oil prices and U.S. consumer inflation data live from FRED (the Federal Reserve's public database), and measures how strongly — and how quickly — oil price shocks pass through into the prices consumers actually pay.

There are two ways to use it:
- **`energy_inflation_engine.py`** — a script that runs the full analysis and saves charts + a results CSV
- **`app.py`** — an interactive Streamlit dashboard where you can change the time period, the lag window, and the inflation measure, and watch the results update live

---

## What I found (2000–2026 data)

I tested oil against three different inflation measures, at every lag from 0 to 12 months. Each one tells a different part of the story:

| Inflation measure | Strongest link | How fast | What it means |
|---|---|---|---|
| **Gasoline CPI** | R² = 0.77, r = 0.88 | 1 month | Oil price changes explain ~77% of gasoline price movement, almost immediately. Makes sense — gasoline basically *is* oil. |
| **Headline CPI** (overall inflation) | R² = 0.40, r = 0.64 | 1 month | Oil explains about 40% of overall inflation's movement, within a month. Big, but not everything — the rest is rent, food, services, wages. |
| **Core CPI** (excludes food & energy) | R² ≈ 0.10, r ≈ 0.32 | ~10 months, weak | By design, core CPI strips energy out. The small effect left over is oil sneaking in *indirectly* — through shipping costs, plastics, airfares — and it takes the better part of a year. |

**The one-sentence takeaway:** an oil shock hits your gas station within a month, shows up meaningfully in overall inflation almost as fast, but barely touches "core" inflation — which is exactly why central banks watch core CPI when they want to see past oil noise.

I also found the result depends on *when* you start measuring: using the full 2000–2026 sample, the best-fit lag for headline CPI is 1 month; start the sample after the 2008 oil spike, and it stretches to ~7 months. Extreme episodes like 2008 and 2021–22 dominate the estimate — a good reminder that a single R² never tells the whole story.

---

## How to read the numbers (no stats degree needed)

- **Pearson r** — how tightly two things move together, from -1 to +1. r = 0.88 (oil vs gasoline CPI) is a very tight relationship; r = 0.32 (oil vs core CPI) is loose.
- **R² (R-squared)** — the share of one thing's movement "explained" by the other. R² = 0.40 means oil accounts for about 40% of headline inflation's variation; the other 60% is everything else in the economy.
- **Lag** — I don't just compare oil and CPI in the same month. I shift oil back by 1, 2, 3... 12 months and re-run the regression each time. The lag where R² peaks tells you the *transmission speed* — how long a shock takes to travel from the oil market to consumer prices.
- **p-value** — the chance you'd see a relationship this strong by pure luck. Essentially zero for gasoline and headline CPI here.

### Why % change, not raw prices?
Both oil prices and CPI drift upward over decades, so raw levels *always* look correlated — even if they had nothing to do with each other. That's called spurious correlation. Converting both to % change removes the shared trend so we're measuring the real relationship.

### Correlation still isn't causation — so I tested further
The dashboard also runs a **Granger causality test**, which asks a sharper question: *do past oil prices help predict future CPI, beyond what CPI's own history already predicts?* And it runs the reverse direction (CPI → oil) as a sanity check — if that were also "significant," it would hint both are driven by something else (like global growth) rather than oil driving inflation. Before running Granger, the app checks stationarity (ADF test), since the test isn't valid without it — and warns you if the data fails.

---

## Skills this project demonstrates

**Technical**
- **Python** — pandas (data wrangling, time series), statsmodels (OLS regression, Granger causality, ADF stationarity tests), matplotlib & Plotly (visualization)
- **Streamlit** — built and deployed an interactive web dashboard with live-refreshing data, caching, and user controls
- **API / data engineering** — pulling and aligning multiple economic time series from FRED's public endpoint, handling missing values and frequency mismatches
- **Git / GitHub** — version control and public deployment

**Analytical**
- Time-series methodology: avoiding spurious correlation, choosing between MoM and YoY changes (and understanding how YoY autocorrelation distorts lag estimates)
- Knowing the difference between correlation, predictive (Granger) causality, and true structural causality — and being honest about which one the analysis supports
- Testing robustness: checking how results change with the sample period instead of reporting one convenient number

**Domain**
- Understanding of inflation mechanics: why gasoline, headline, and core CPI respond differently to energy shocks, and why policymakers track core CPI

---

## Run it yourself

```bash
git clone https://github.com/YOUR-USERNAME/energy-inflation-correlation-engine.git
cd energy-inflation-correlation-engine
pip install -r requirements.txt

# Option 1: the script (saves charts + CSV to the folder)
python energy_inflation_engine.py

# Option 2: the interactive dashboard
streamlit run app.py
```

No API key needed — FRED's endpoint is public. Data refreshes automatically: oil prices update daily on FRED, CPI once a month.

---

## What's in the repo

| File | What it is |
|---|---|
| `app.py` | Interactive Streamlit dashboard (regression + Granger causality) |
| `energy_inflation_engine.py` | Standalone analysis script |
| `energy_inflation_results.csv` | Full results table from my run (all lags × all CPI measures) |
| `lag_vs_rsquared.png` | Chart: how oil's explanatory power changes with lag, per CPI measure |
| `oil_vs_cpi_overlay.png` | Chart: oil vs headline CPI % change, 2000–2026 |
| `requirements.txt` | Dependencies |

---

## Limitations & what I'd build next

- This measures **predictive** relationships, not structural causation — a full causal claim would need a VAR/SVAR model with identification assumptions.
- Results are sensitive to extreme episodes (2008, 2020, 2022). A rolling-window version would show whether pass-through strength has changed over time.
- U.S.-only, WTI-only for now; Brent and other countries' CPI would make a nice comparison.
- Ideas on the list: rolling-window regressions, Brent vs WTI, a forecast module using the fitted lag structure.

## License

MIT — free to use, learn from, and build on.
