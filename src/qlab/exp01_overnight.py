"""Experiment 01 — Overnight vs intraday decomposition of QQQ, tested with real costs.

Hypothesis (from the literature): most of QQQ's return happens overnight (close->open),
so an "overnight-only" strategy has a huge GROSS Sharpe. Honest question: does any of it
survive realistic per-trade costs? (AlphaArchitect + the failed NSPY/NIWM ETFs say no.)
This confirms/denies it ourselves before chasing it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252
DATA = Path(__file__).resolve().parents[2] / "data" / "qqq_daily.csv"


def load_qqq() -> pd.DataFrame:
    if DATA.exists():
        df = pd.read_csv(DATA, parse_dates=["Date"], index_col="Date")
    else:
        raw = yf.download("QQQ", start="1999-03-10", auto_adjust=False, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        df = raw[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna()
        df.index.name = "Date"
        DATA.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(DATA)
    return df


def metrics(daily: pd.Series) -> dict[str, float]:
    d = daily.dropna()
    eq = (1 + d).cumprod()
    years = len(d) / TRADING_DAYS
    cagr = eq.iloc[-1] ** (1 / years) - 1
    sharpe = d.mean() / d.std() * np.sqrt(TRADING_DAYS) if d.std() > 0 else np.nan
    mdd = (eq / eq.cummax() - 1).min()
    return {"CAGR": cagr, "Sharpe": sharpe, "MaxDD": mdd, "end$300k": 300_000 * eq.iloc[-1]}


def main() -> None:
    df = load_qqq()
    c, o = df["Close"], df["Open"]
    overnight = (o / c.shift(1) - 1).rename("overnight")
    intraday = (c / o - 1).rename("intraday")
    c2c = (c / c.shift(1) - 1).rename("buyhold")

    print(f"QQQ {df.index[0].date()} -> {df.index[-1].date()}  ({len(df)} days)\n")
    print(f"{'strategy':28s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'$300k end':>14s}")

    def show(name: str, s: pd.Series) -> None:
        m = metrics(s)
        print(f"{name:28s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% "
              f"{m['end$300k']:>14,.0f}")

    show("BuyHold (close-close)", c2c)
    show("Overnight-only (GROSS)", overnight)
    show("Intraday-only (GROSS)", intraday)
    print("  --- overnight-only NET of per-side trading cost (2 sides/day) ---")
    for bps in (1, 2, 5, 10):
        show(f"Overnight net {bps}bps/side", overnight - 2 * bps / 10_000.0)
    print("\nNote: raw-price decomposition (ignores ~0.6%/yr QQQ dividend, minor). "
          "Overnight-only trades every day (2 fills); buy-hold trades ~never.")


if __name__ == "__main__":
    main()
