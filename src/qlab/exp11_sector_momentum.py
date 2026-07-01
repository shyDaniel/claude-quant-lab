"""Experiment 11 — Sector-ETF momentum: is the momentum edge REAL (survivorship-free)?

The AI-basket momentum (exp02) was survivorship-biased (today's winners). Sector SPDRs are
survivorship-FREE (sectors don't disappear) and fully executable. If cross-sectional
momentum on sectors beats buy-hold risk-adjusted, the edge is real; if not, exp02 was bias.
Rank 9 sectors by 12-mo momentum monthly, hold top-3 (positive-momentum filter, else cash).
Compare vs SPY & QQQ buy-hold and vs my core.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252
SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU"]
TOP_N, LOOKBACK, COST_BPS = 3, 252, 10.0
DATA = Path(__file__).resolve().parents[2] / "data" / "sectors.csv"


def load() -> pd.DataFrame:
    if DATA.exists():
        return pd.read_csv(DATA, parse_dates=["Date"], index_col="Date")
    raw = yf.download(SECTORS + ["SPY", "QQQ"], start="1999-01-01", auto_adjust=True, progress=False)
    px = (raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw).dropna(how="all")
    DATA.parent.mkdir(parents=True, exist_ok=True)
    px.to_csv(DATA)
    return px


def metrics(d: pd.Series) -> dict[str, float]:
    d = d.dropna()
    eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS),
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(TRADING_DAYS).min()}


def sector_momentum(px: pd.DataFrame, names: list[str]) -> pd.Series:
    mom = (px[names] / px[names].shift(LOOKBACK) - 1).shift(1)
    me = px.index.to_series().groupby(px.index.to_period("M")).transform("max") == px.index
    w = pd.DataFrame(np.nan, index=px.index, columns=names)
    for date in px.index[me]:
        row = pd.Series(0.0, index=names)
        cand = mom.loc[date].dropna()
        cand = cand[cand > 0.0]
        row[cand.sort_values(ascending=False).head(TOP_N).index] = 1.0 / TOP_N  # remainder cash
        w.loc[date] = row
    w = w.ffill().fillna(0.0)
    r = px[names].pct_change().fillna(0.0)
    return (w.shift(1).fillna(0.0) * r).sum(axis=1) - w.diff().abs().sum(axis=1).fillna(0.0) * COST_BPS / 10_000.0


def main() -> None:
    px = load()
    names = [c for c in SECTORS if c in px.columns]
    px = px.dropna(subset=names)
    print(f"Sector momentum {px.index[0].date()} -> {px.index[-1].date()} ({len(names)} sectors, survivorship-free)\n")
    print(f"{'strategy':30s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s}")

    def show(name: str, s: pd.Series) -> None:
        m = metrics(s)
        print(f"{name:30s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% {m['w12mo']*100:6.1f}%")

    show("SPY buy-hold", px["SPY"].pct_change().fillna(0.0))
    show("QQQ buy-hold", px["QQQ"].pct_change().fillna(0.0))
    show("Sectors equal-weight hold", px[names].pct_change().fillna(0.0).mean(axis=1))
    show(f"Sector-momentum top{TOP_N}", sector_momentum(px, names))
    ann = sector_momentum(px, names)
    print("\nRead: does clean sector momentum beat SPY/QQQ on Sharpe/drawdown? "
          "If ~tie or worse, the exp02 AI 'edge' was survivorship bias.")


if __name__ == "__main__":
    main()
