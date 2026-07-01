"""Experiment 05 — Refine the FINAL rule: rebalance frequency x risk-off asset.

Confirm the simplest, lowest-risk configuration of "QQQ 12-mo momentum -> risk-off".
- Frequency: monthly (simplest) vs weekly (does more frequent checking cut the -29% DD?).
- Risk-off asset: cash(0%) vs BIL (T-bills) vs IEF (Treasuries).
Lower drawdown + higher Sharpe + still-simple wins; watch turnover (tax/cost).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
DATA = Path(__file__).resolve().parents[2] / "data" / "core_assets.csv"


def metrics(daily: pd.Series) -> dict[str, float]:
    d = daily.dropna()
    eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS),
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(TRADING_DAYS).min()}


def run(px: pd.DataFrame, freq: str, off: str, cost_bps: float = 5.0) -> tuple[pd.Series, float]:
    qqq = px["QQQ"]
    mom_on = (qqq / qqq.shift(252) - 1 > 0).shift(1).fillna(False)
    idx = px.index
    if freq == "M":
        mask = idx.to_series().groupby(idx.to_period("M")).transform("max") == idx
    else:  # weekly (last obs each ISO week)
        mask = idx.to_series().groupby([idx.isocalendar().year, idx.isocalendar().week]).transform("max") == idx
    target = pd.Series(np.nan, index=idx)
    target[mask] = mom_on[mask].astype(float)
    target = target.ffill().fillna(0.0)
    qqq_r = qqq.pct_change().fillna(0.0)
    off_r = pd.Series(0.0, index=idx) if off == "CASH" else px[off].pct_change().fillna(0.0)
    w = target.shift(1).fillna(0.0)
    port = w * qqq_r + (1 - w) * off_r - target.diff().abs().fillna(0.0) * cost_bps / 10_000.0
    return port, target.diff().abs().sum() / (len(idx) / TRADING_DAYS)


def main() -> None:
    px = pd.read_csv(DATA, parse_dates=["Date"], index_col="Date")
    px = px.loc["2007":]  # BIL exists from 2007 for a fair 3-way risk-off compare
    print(f"Window {px.index[0].date()} -> {px.index[-1].date()} (BIL available)\n")
    print(f"{'config':26s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s} {'turn':>6s}")
    print(f"{'QQQ buy-hold':26s} " + fmt(metrics(px['QQQ'].pct_change().fillna(0.0)), 0.0))
    for freq in ("M", "W"):
        for off in ("CASH", "BIL", "IEF"):
            s, t = run(px, freq, off)
            print(f"{('12mo-mom '+freq+' -> '+off):26s} " + fmt(metrics(s), t))


def fmt(m: dict[str, float], t: float) -> str:
    return (f"{m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% "
            f"{m['w12mo']*100:6.1f}% {t:5.1f}x")


if __name__ == "__main__":
    main()
