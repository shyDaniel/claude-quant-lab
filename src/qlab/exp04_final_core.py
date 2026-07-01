"""Experiment 04 — Lock the FINAL simplest, lowest-risk core.

Compare the simplest QQQ trend rules over a long window, OOS-split, pick the one with the
best ROBUST risk-adjusted return + shallowest drawdown + lowest turnover (tax proxy).
Candidates (all monthly-checked = simplest to run by hand):
  - QQQ buy-hold (bar)
  - QQQ 200d-SMA trend (cash when below)
  - QQQ 12-mo momentum (cash when negative)          <- Codex core
  - QQQ 12-mo momentum, IEF Treasuries when off       <- dual-momentum lite
  - QQQ 200d-SMA, IEF when off
Lowest risk + simplest wins. Turnover reported as a tax proxy (lower = friendlier).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252
DATA = Path(__file__).resolve().parents[2] / "data" / "core_assets.csv"


def load() -> pd.DataFrame:
    if DATA.exists():
        return pd.read_csv(DATA, parse_dates=["Date"], index_col="Date")
    raw = yf.download(["QQQ", "IEF", "BIL"], start="2004-01-01", auto_adjust=True, progress=False)
    px = (raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw).dropna(how="all")
    DATA.parent.mkdir(parents=True, exist_ok=True)
    px.to_csv(DATA)
    return px


def metrics(daily: pd.Series) -> dict[str, float]:
    d = daily.dropna()
    if len(d) < 30:
        return {k: float("nan") for k in ("CAGR", "Sharpe", "MaxDD", "w12mo")}
    eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS) if d.std() > 0 else np.nan,
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(TRADING_DAYS).min()}


def month_end(idx: pd.DatetimeIndex) -> pd.Series:
    return idx.to_series().groupby(idx.to_period("M")).transform("max") == idx


def trend_strategy(px: pd.DataFrame, signal_on: pd.Series, off_asset: str, cost_bps: float = 5.0) -> tuple[pd.Series, float]:
    """signal_on True => hold QQQ; else hold off_asset ('CASH' or a ticker). Monthly rebalance."""
    me = month_end(px.index)
    target = pd.Series(np.nan, index=px.index)
    target[me] = signal_on[me].astype(float)         # 1 = QQQ, 0 = off
    target = target.ffill().fillna(0.0)
    qqq_r = px["QQQ"].pct_change().fillna(0.0)
    off_r = pd.Series(0.0, index=px.index) if off_asset == "CASH" else px[off_asset].pct_change().fillna(0.0)
    w_qqq = target.shift(1).fillna(0.0)
    port = w_qqq * qqq_r + (1 - w_qqq) * off_r
    turn = target.diff().abs().fillna(0.0)            # 0->1 or 1->0 switch
    port = port - turn * cost_bps / 10_000.0
    ann_turn = turn.sum() / (len(px) / TRADING_DAYS)
    return port, ann_turn


def main() -> None:
    px = load()
    qqq = px["QQQ"]
    sma_on = (qqq > qqq.rolling(200).mean()).shift(1).fillna(False)
    mom_on = (qqq / qqq.shift(252) - 1 > 0).shift(1).fillna(False)
    qqq_r = qqq.pct_change().fillna(0.0)

    strat = {}
    strat["QQQ buy-hold"] = (qqq_r, 0.0)
    strat["QQQ 200d-SMA -> cash"] = trend_strategy(px, sma_on, "CASH")
    strat["QQQ 12mo-mom -> cash"] = trend_strategy(px, mom_on, "CASH")
    strat["QQQ 12mo-mom -> IEF"] = trend_strategy(px, mom_on, "IEF")
    strat["QQQ 200d-SMA -> IEF"] = trend_strategy(px, sma_on, "IEF")

    print(f"Window {px.index[0].date()} -> {px.index[-1].date()}")

    def table(title: str, sl: slice) -> None:
        print(f"\n=== {title} ===")
        print(f"{'strategy':24s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s} {'turn':>6s}")
        for name, (s, t) in strat.items():
            m = metrics(s.loc[sl])
            print(f"{name:24s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% "
                  f"{m['w12mo']*100:6.1f}% {t:5.1f}x")

    table("FULL", slice(None))
    table("OOS-A 2004-2014", slice("2004", "2014"))
    table("OOS-B 2015-2026", slice("2015", "2026"))


if __name__ == "__main__":
    main()
