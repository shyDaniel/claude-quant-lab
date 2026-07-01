"""Experiment 03 — De-bias + de-risk the AI/tech momentum (toward a FINAL simple low-risk rule).

Goal lens: simplest + lowest risk, proven by data. Two checks:
  1. OUT-OF-SAMPLE split: does momentum beat equal-weight in BOTH halves (2013-19, 2020-26)?
     If it only works in one half, it's fragile.
  2. RISK OVERLAY: gate the momentum basket with a simple QQQ 200-day trend filter
     (hold basket only when QQQ > 200d SMA, else cash). Does it cut the -39% drawdown
     while keeping the edge? That is the low-risk refinement.
Compared vs QQQ buy-hold and a QQQ 200d-SMA trend rule (Codex-core proxy).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
BASKET = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "AMD",
          "ADBE", "CRM", "ORCL", "QCOM", "TSLA", "NFLX"]
TOP_N, LOOKBACK, COST_BPS = 5, 126, 10.0
DATA = Path(__file__).resolve().parents[2] / "data" / "basket_adjclose.csv"


def metrics(daily: pd.Series) -> dict[str, float]:
    d = daily.dropna()
    if len(d) < 30:
        return {k: float("nan") for k in ("CAGR", "Sharpe", "MaxDD", "w12mo")}
    eq = (1 + d).cumprod()
    years = len(d) / TRADING_DAYS
    return {"CAGR": eq.iloc[-1] ** (1 / years) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS) if d.std() > 0 else np.nan,
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(TRADING_DAYS).min()}


def momentum_weights(px: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    mom = (px[names] / px[names].shift(LOOKBACK) - 1).shift(1)
    me = px.index.to_series().groupby(px.index.to_period("M")).transform("max") == px.index
    w = pd.DataFrame(np.nan, index=px.index, columns=names)
    for date in px.index[me]:
        row = pd.Series(0.0, index=names)
        cand = mom.loc[date].dropna()
        cand = cand[cand > 0.0]
        row[cand.sort_values(ascending=False).head(TOP_N).index] = 1.0 / TOP_N
        w.loc[date] = row
    return w.ffill().fillna(0.0)


def sim(px: pd.DataFrame, names: list[str], w: pd.DataFrame, cost_bps: float = COST_BPS) -> pd.Series:
    rets = px[names].pct_change().fillna(0.0)
    gross = (w.shift(1).fillna(0.0) * rets).sum(axis=1)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return gross - turn * cost_bps / 10_000.0


def main() -> None:
    px = pd.read_csv(DATA, parse_dates=["Date"], index_col="Date")
    names = [c for c in BASKET if c in px.columns]
    qqq = px["QQQ"]
    qqq_ret = qqq.pct_change().fillna(0.0)

    # QQQ 200d-SMA trend gate (simple, low-risk)
    trend_on = (qqq > qqq.rolling(200).mean()).shift(1).fillna(False)
    w = momentum_weights(px, names)
    w_gated = w.mul(trend_on.astype(float), axis=0)          # flat (cash) when QQQ below 200d SMA

    strategies = {
        "QQQ buy-hold": qqq_ret,
        "QQQ 200d-SMA trend (core proxy)": qqq_ret.where(trend_on, 0.0),
        "AI-momentum top5": sim(px, names, w),
        "AI-momentum + QQQ-trend gate": sim(px, names, w_gated),
        "Basket equal-weight hold": px[names].pct_change().fillna(0.0).mean(axis=1),
    }

    def table(title: str, sl: slice) -> None:
        print(f"\n=== {title} ===")
        print(f"{'strategy':34s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s}")
        for name, s in strategies.items():
            m = metrics(s.loc[sl])
            print(f"{name:34s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} "
                  f"{m['MaxDD']*100:7.1f}% {m['w12mo']*100:6.1f}%")

    table("FULL 2013-2026", slice(None))
    table("OOS-A 2013-2019", slice("2013", "2019"))
    table("OOS-B 2020-2026", slice("2020", "2026"))
    gturn = w_gated.diff().abs().sum(axis=1).sum() / (len(px) / TRADING_DAYS)
    print(f"\nGated turnover: {gturn:.2f}x/yr. Gate = hold basket only when QQQ>200d SMA, else cash(0%).")


if __name__ == "__main__":
    main()
