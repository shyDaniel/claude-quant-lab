"""Experiment 06 — Does a small AI/tech sleeve improve the FINAL core's frontier?

Blend the locked core (QQQ 12mo-mom -> T-bills, monthly) with the AI/tech momentum sleeve
(exp02). Honest question for the goal (simplest + lowest risk): does 10-20% AI improve
risk-adjusted return without wrecking drawdown/simplicity? Survivorship caveat still applies
(the AI sleeve's history is inflated), so read Sharpe/DD, not the raw CAGR, and haircut.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
BASKET = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "AMD",
          "ADBE", "CRM", "ORCL", "QCOM", "TSLA", "NFLX"]
ROOT = Path(__file__).resolve().parents[2] / "data"


def metrics(d: pd.Series) -> dict[str, float]:
    d = d.dropna()
    eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS),
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(TRADING_DAYS).min()}


def month_end(idx: pd.DatetimeIndex) -> pd.Series:
    return idx.to_series().groupby(idx.to_period("M")).transform("max") == idx


def core_returns(core: pd.DataFrame) -> pd.Series:
    """QQQ 12mo-mom -> BIL, monthly."""
    q = core["QQQ"]
    on = (q / q.shift(252) - 1 > 0).shift(1).fillna(False)
    me = month_end(core.index)
    tgt = pd.Series(np.nan, index=core.index)
    tgt[me] = on[me].astype(float)
    tgt = tgt.ffill().fillna(0.0)
    qr = q.pct_change().fillna(0.0)
    br = core["BIL"].pct_change().fillna(0.0)
    w = tgt.shift(1).fillna(0.0)
    return w * qr + (1 - w) * br - tgt.diff().abs().fillna(0.0) * 5 / 10_000.0


def ai_returns(basket: pd.DataFrame, names: list[str]) -> pd.Series:
    mom = (basket[names] / basket[names].shift(126) - 1).shift(1)
    me = month_end(basket.index)
    w = pd.DataFrame(np.nan, index=basket.index, columns=names)
    for date in basket.index[me]:
        row = pd.Series(0.0, index=names)
        cand = mom.loc[date].dropna()
        cand = cand[cand > 0.0]
        row[cand.sort_values(ascending=False).head(5).index] = 1 / 5
        w.loc[date] = row
    w = w.ffill().fillna(0.0)
    r = basket[names].pct_change().fillna(0.0)
    return (w.shift(1).fillna(0.0) * r).sum(axis=1) - w.diff().abs().sum(axis=1).fillna(0.0) * 10 / 10_000.0


def main() -> None:
    core = pd.read_csv(ROOT / "core_assets.csv", parse_dates=["Date"], index_col="Date").loc["2013":]
    basket = pd.read_csv(ROOT / "basket_adjclose.csv", parse_dates=["Date"], index_col="Date")
    names = [c for c in BASKET if c in basket.columns]
    core_r = core_returns(core).reindex(basket.index).fillna(0.0)
    ai_r = ai_returns(basket, names)
    qqq_r = basket["QQQ"].pct_change().fillna(0.0)

    print(f"Window {basket.index[0].date()} -> {basket.index[-1].date()} (AI sleeve survivorship-biased)\n")
    print(f"{'blend':26s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s}")

    def show(name: str, r: pd.Series) -> None:
        m = metrics(r)
        print(f"{name:26s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% {m['w12mo']*100:6.1f}%")

    show("QQQ buy-hold", qqq_r)
    show("100% core (final)", core_r)
    for ai_w in (0.10, 0.20, 0.30):
        show(f"{int((1-ai_w)*100)}% core + {int(ai_w*100)}% AI", (1 - ai_w) * core_r + ai_w * ai_r)
    show("100% AI sleeve", ai_r)


if __name__ == "__main__":
    main()
