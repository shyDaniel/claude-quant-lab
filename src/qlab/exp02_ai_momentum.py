"""Experiment 02 — Cross-sectional momentum on an AI/tech basket vs QQQ.

The user's actual angle (Codex botched its AI sleeve). Honest design:
- Benchmarks: (a) QQQ buy-hold = the bar; (b) EQUAL-WEIGHT buy-hold of the SAME basket
  = isolates the momentum SIGNAL's value from survivorship bias in the basket choice.
- Strategy: monthly, rank basket by 6-mo momentum, hold top-N positive-momentum names
  equal-weight, remainder in cash. No lookahead (signals shifted). Realistic costs.
- SURVIVORSHIP CAVEAT: the basket is today's tech winners → biased UP vs QQQ. The
  momentum-vs-EW-hold comparison is the less-biased read.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252
START = "2013-01-01"
BASKET = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "AMD",
          "ADBE", "CRM", "ORCL", "QCOM", "TSLA", "NFLX"]
TOP_N = 5
LOOKBACK = 126        # 6-month momentum
COST_BPS = 10.0       # per unit turnover, one-way
DATA = Path(__file__).resolve().parents[2] / "data" / "basket_adjclose.csv"


def load_prices() -> pd.DataFrame:
    if DATA.exists():
        return pd.read_csv(DATA, parse_dates=["Date"], index_col="Date")
    raw = yf.download(BASKET + ["QQQ"], start=START, auto_adjust=True, progress=False)
    px = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    px = px.dropna(how="all")
    DATA.parent.mkdir(parents=True, exist_ok=True)
    px.to_csv(DATA)
    return px


def metrics(daily: pd.Series) -> dict[str, float]:
    d = daily.dropna()
    eq = (1 + d).cumprod()
    years = len(d) / TRADING_DAYS
    cagr = eq.iloc[-1] ** (1 / years) - 1
    sharpe = d.mean() / d.std() * np.sqrt(TRADING_DAYS) if d.std() > 0 else np.nan
    mdd = (eq / eq.cummax() - 1).min()
    worst12 = eq.pct_change(TRADING_DAYS).min()
    return {"CAGR": cagr, "Sharpe": sharpe, "MaxDD": mdd, "w12mo": worst12,
            "end$300k": 300_000 * eq.iloc[-1]}


def build_weights(px: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    mom = (px[names] / px[names].shift(LOOKBACK) - 1).shift(1)   # no lookahead
    month_end = px.index.to_series().groupby(px.index.to_period("M")).transform("max") == px.index
    w = pd.DataFrame(np.nan, index=px.index, columns=names)      # NaN => carry prior target
    for date in px.index[month_end]:
        row = pd.Series(0.0, index=names)                        # explicit zeros = remainder cash
        cand = mom.loc[date].dropna()
        cand = cand[cand > 0.0]                                  # absolute-momentum filter
        top = cand.sort_values(ascending=False).head(TOP_N).index
        row[top] = 1.0 / TOP_N
        w.loc[date] = row                                        # set FULL target incl zeros
    return w.ffill().fillna(0.0)


def simulate(px: pd.DataFrame, names: list[str], w: pd.DataFrame, cost_bps: float) -> pd.Series:
    rets = px[names].pct_change().fillna(0.0)
    applied = w.shift(1).fillna(0.0)
    gross = (applied * rets).sum(axis=1)
    turnover = w.diff().abs().sum(axis=1).fillna(0.0)
    return gross - turnover * cost_bps / 10_000.0


def main() -> None:
    px = load_prices()
    names = [c for c in BASKET if c in px.columns]
    print(f"Basket {px.index[0].date()} -> {px.index[-1].date()}  ({len(names)} names)\n")
    print(f"{'strategy':30s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s} {'$300k end':>13s}")

    def show(name: str, s: pd.Series) -> None:
        m = metrics(s)
        print(f"{name:30s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% "
              f"{m['w12mo']*100:6.1f}% {m['end$300k']:>13,.0f}")

    qqq = px["QQQ"].pct_change().fillna(0.0)
    ew = px[names].pct_change().fillna(0.0).mean(axis=1)          # equal-weight basket hold
    w = build_weights(px, names)
    mom_net = simulate(px, names, w, COST_BPS)
    mom_gross = simulate(px, names, w, 0.0)

    show("QQQ buy-hold (bar)", qqq)
    show("Basket equal-weight hold", ew)
    show(f"AI-momentum top{TOP_N} GROSS", mom_gross)
    show(f"AI-momentum top{TOP_N} net {COST_BPS:.0f}bps", mom_net)
    print(f"\nAvg names held: {(w > 0).sum(axis=1).replace(0, np.nan).mean():.1f}  "
          f"| annual turnover: {w.diff().abs().sum(axis=1).sum() / (len(px)/TRADING_DAYS):.2f}x")
    print("SURVIVORSHIP CAVEAT: basket = today's tech winners → biased vs QQQ. "
          "Key read = momentum vs equal-weight-hold (same basket).")


if __name__ == "__main__":
    main()
