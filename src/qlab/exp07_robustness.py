"""Experiment 07 — Robustness battery: is the core rule REAL or data-mined?

Three overfitting stress tests (the honest standard of proof — not "best in the world"):
  A. LOOKBACK sweep: does it depend on the exact 12-month lookback, or work across 3-15mo?
  B. REBALANCE-DAY sweep: does it depend on checking on month-end, or any consistent day?
  C. CROSS-ASSET: apply the SAME rule to SPY (and QQQ). If it reduces drawdown on BOTH,
     the edge is the universal trend effect, not a QQQ curve-fit.
If the rule is stable across A/B and works on C, it's robust — the real ceiling of proof.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252
ROOT = Path(__file__).resolve().parents[2] / "data"


def metrics(d: pd.Series) -> dict[str, float]:
    d = d.dropna()
    eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS),
            "MaxDD": (eq / eq.cummax() - 1).min()}


def rule(px: pd.DataFrame, risk: str, off: str, lookback: int = 252, kth: int = -1) -> pd.Series:
    """Own `risk` when its `lookback`-day momentum > 0, else `off`. Rebalance on the kth
    trading day of each month (kth=-1 => month-end)."""
    r = px[risk]
    on = (r / r.shift(lookback) - 1 > 0).shift(1).fillna(False)
    grp = px.index.to_period("M")
    pos = px.index.to_series().groupby(grp).cumcount()
    size = px.index.to_series().groupby(grp).transform("size")
    mask = (pos == (size - 1)) if kth == -1 else (pos == np.minimum(kth, size - 1))
    tgt = pd.Series(np.nan, index=px.index)
    tgt[mask.values] = on[mask.values].astype(float)
    tgt = tgt.ffill().fillna(0.0)
    rr = r.pct_change().fillna(0.0)
    orr = pd.Series(0.0, index=px.index) if off == "CASH" else px[off].pct_change().fillna(0.0)
    w = tgt.shift(1).fillna(0.0)
    return w * rr + (1 - w) * orr - tgt.diff().abs().fillna(0.0) * 5 / 10_000.0


def load_spy() -> pd.Series:
    f = ROOT / "spy_daily.csv"
    if f.exists():
        return pd.read_csv(f, parse_dates=["Date"], index_col="Date")["SPY"]
    raw = yf.download("SPY", start="2004-01-01", auto_adjust=True, progress=False)
    close = raw["Close"]
    s = (close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close).dropna()
    s.name = "SPY"
    s.to_frame().to_csv(f)
    return s


def main() -> None:
    px = pd.read_csv(ROOT / "core_assets.csv", parse_dates=["Date"], index_col="Date")
    px = px.join(load_spy(), how="left")

    print("A. LOOKBACK sweep (QQQ mom -> BIL, monthly). Stable => not overfit to '12 months'.")
    print(f"   {'lookback':10s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s}")
    for lb, lab in [(63, "3mo"), (126, "6mo"), (189, "9mo"), (252, "12mo"), (315, "15mo")]:
        m = metrics(rule(px, "QQQ", "BIL", lookback=lb))
        print(f"   {lab:10s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}%")

    print("\nB. REBALANCE-DAY sweep (12mo, QQQ -> BIL). Stable => not a month-end artifact.")
    print(f"   {'check day':10s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s}")
    for k, lab in [(0, "1st"), (7, "8th"), (14, "15th"), (-1, "month-end")]:
        m = metrics(rule(px, "QQQ", "BIL", kth=k))
        print(f"   {lab:10s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}%")

    print("\nC. CROSS-ASSET (same 12mo rule). Works on BOTH => real trend edge, not QQQ fit.")
    print(f"   {'asset/strat':22s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s}")
    for a in ("QQQ", "SPY"):
        bh = metrics(px[a].pct_change().fillna(0.0))
        rl = metrics(rule(px, a, "BIL"))
        print(f"   {a+' buy-hold':22s} {bh['CAGR']*100:6.1f}% {bh['Sharpe']:7.2f} {bh['MaxDD']*100:7.1f}%")
        print(f"   {a+' 12mo-mom->BIL':22s} {rl['CAGR']*100:6.1f}% {rl['Sharpe']:7.2f} {rl['MaxDD']*100:7.1f}%")


if __name__ == "__main__":
    main()
