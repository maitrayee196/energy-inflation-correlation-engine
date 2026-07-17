# Energy Inflation Correlation Engine

**Maitrayee Vishnu** | MS Finance candidate, Stevens Institute of Technology | Ex FP&A Associate, JPMorgan Chase

[LinkedIn](https://www.linkedin.com/in/maitrayee-vishnu) · [Portfolio](https://maitrayee196.github.io/Maitrayee_Portfolio/) · [GitHub](https://github.com/maitrayee196)

### 🔴 [Live demo: try the dashboard here](https://energy-inflation-correlation-engine-wcrbxyajkczqbrgjnhosin.streamlit.app/)

## The problem I wanted to solve

Everyone knows that when oil prices spike, inflation follows. You hear it on the news, you feel it at the gas station. But there is a gap in that story that nobody quantifies clearly. How long does it actually take for an oil shock to reach consumer prices? And how much of inflation is really oil, versus everything else in the economy?

That gap matters. If you work in finance, the answer changes how you read an inflation print. If oil jumped last month, is this month's hot CPI number a warning sign or just oil passing through? The Federal Reserve watches core CPI precisely because it strips oil out. I wanted to measure that relationship myself, with real data, instead of taking it on faith.

## What this project does

It pulls crude oil prices and three measures of U.S. consumer inflation directly from FRED, the Federal Reserve's public database, covering 2000 to today. Then it asks a simple question at every time gap from 0 to 12 months: if oil moved this month, how well does that predict where inflation goes 1 month later? 2 months later? 6 months later?

The lag where the relationship peaks tells you the transmission speed of an oil shock through the economy. The strength of the relationship tells you how much of inflation oil actually explains.

There are two ways to use it. A Python script runs the full analysis and saves charts plus a results file. An interactive dashboard lets you change the time period, the inflation measure and the lag window, and watch the answer change live.

## What I found

Oil hits different parts of inflation at very different speeds, and the pattern makes economic sense.

**Gasoline prices react almost instantly.** Oil explains about 77% of gasoline CPI movement within one month, with a correlation of 0.88. No surprise there, gasoline basically is oil.

**Overall inflation follows fast, but oil is not the whole story.** Oil explains roughly 40% of headline CPI movement within one month. Meaningful, but the other 60% is rent, food, services and wages.

**Core inflation barely notices.** Core CPI excludes food and energy by design, so what remains is oil sneaking in indirectly through shipping costs, plastics and airfares. That effect is small, around 10%, and takes most of a year to show up.

This is exactly why central banks watch core CPI when they want to see past oil noise, and now I have the numbers behind that intuition.

One more finding surprised me. The answer depends heavily on when you start measuring. Using the full 2000 to 2026 sample, oil's strongest effect on headline CPI comes at a 1 month lag. Start the sample after the 2008 oil spike and it stretches to about 7 months. Extreme episodes like 2008 and the 2021 to 2022 surge dominate the estimate. A single number never tells the whole story, and the dashboard lets you see that for yourself by moving the start date.

## How I built it

The analysis rests on getting the statistics right, because this topic is full of traps.

First trap: both oil prices and CPI drift upward over decades, so their raw levels always look correlated even when they have nothing to do with each other. Statisticians call this spurious correlation. I converted both series to percentage change to remove the shared trend and measure the real relationship.

Second trap: correlation is not causation. So beyond the regressions, the dashboard runs a Granger causality test, which asks a sharper question. Do past oil prices help predict future CPI beyond what CPI's own history already predicts? It also tests the reverse direction, CPI predicting oil, as a sanity check. If both directions looked significant, that would suggest some third force drives both. And before any of that, the app checks stationarity with an ADF test, because the Granger test is not valid without it, and warns you when the data fails.

Third trap: year over year data looks smooth and convincing, but each data point shares eleven months with its neighbor, which quietly distorts lag estimates. The dashboard lets you switch between year over year and month over month views so you can see the difference yourself.

## Tech stack

**Python** does all the work. Pandas handles the time series wrangling, statsmodels runs the OLS regressions, Granger causality and ADF stationarity tests, and matplotlib and Plotly draw the charts.

**Streamlit** turns the analysis into a live web dashboard with caching, user controls and hourly data refresh, deployed free on Streamlit Community Cloud straight from this repo.

**FRED's public API** supplies the data. No key needed. Oil prices update daily, CPI monthly, and the dashboard picks up new data automatically.

**Git and GitHub** for version control and publishing.

## What this project says about how I work

I came to this from a finance background, not a software one. What I wanted to show is that I can take a question a portfolio manager or FP&A team would actually ask, find the right public data, apply the statistics honestly including their limitations, and ship something interactive that anyone can use without installing a thing.

The honesty part matters most to me. It would have been easy to report one impressive R² and stop. Instead the project surfaces its own caveats: the sample period sensitivity, the year over year distortion, the difference between correlation and predictive causality. In my experience at JPMorgan, the analysis people trust is the one that shows its weaknesses.

## What is in this repo

`app.py` is the interactive dashboard. `energy_inflation_engine.py` is the standalone script. `energy_inflation_results.csv` holds the full results table from my run. The two PNG files are the key charts. `requirements.txt` lists the dependencies.

To run it yourself:

```
git clone https://github.com/maitrayee196/energy-inflation-correlation-engine.git
cd energy-inflation-correlation-engine
pip install -r requirements.txt
streamlit run app.py
```

## Where I would take it next

A rolling window version would show whether oil's grip on inflation has strengthened or weakened over the decades. Adding Brent crude and other countries' CPI would test whether the pattern holds outside the U.S. And the fitted lag structure could power a simple forecasting module: given this month's oil move, here is the expected drag on next quarter's CPI.

## Author

**Maitrayee Vishnu** | MS Finance candidate, Stevens Institute of Technology | Ex FP&A Associate, JPMorgan Chase

[LinkedIn](https://www.linkedin.com/in/maitrayee-vishnu) · [Portfolio](https://maitrayee196.github.io/Maitrayee_Portfolio/) · [GitHub](https://github.com/maitrayee196)

## License

MIT. Free to use, learn from and build on.
