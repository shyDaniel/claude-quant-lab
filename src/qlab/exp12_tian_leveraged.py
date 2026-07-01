"""Experiment 12 — Verify Tian Compounding's headline claim (trend-filtered leverage).

His #1 idea: 60% QQQ + 30% QLD(2x) + 10% TQQQ(3x), gated by SMA200 (+hysteresis) ->
claims ~2x QQQ's return with LOWER drawdown. That would genuinely beat QQQ on return AND
risk. Test it HONESTLY: simulate the leveraged ETFs from QQQ daily returns with realistic
expense + financing drag (captures volatility decay via daily compounding), run through
dot-com + GFC (1999-2026), net of costs, vs QQQ buy-hold and my core.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
ROOT = Path(__file__).resolve().parents[2] / "data"
EXPENSE = 0.0095      # leveraged ETF expense ratio
FINANCE = 0.03        # annual financing cost on borrowed exposure
CASH_YLD = 0.02       # risk-off cash proxy (pre-BIL era)


def lev_etf(qqq_ret: pd.Series, L: float) -> pd.Series:
    """Daily-reset Lx ETF: L*daily return minus expense + financing on (L-1) borrow."""
    drag = (EXPENSE + (L - 1) * FINANCE) / TRADING_DAYS
    return L * qqq_ret - drag


def metrics(daily: pd.Series) -> dict[str, float]:
    d = daily.dropna()
    eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS),
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(TRADING_DAYS).min(),
            "end": 300_000 * eq.iloc[-1]}


def main() -> None:
    df = pd.read_csv(ROOT / "qqq_daily.csv", parse_dates=["Date"], index_col="Date")
    q = df["Close"]
    qr = q.pct_change().fillna(0.0)
    qld_r, tqqq_r = lev_etf(qr, 2.0), lev_etf(qr, 3.0)
    cash_r = pd.Series(CASH_YLD / TRADING_DAYS, index=q.index)

    sma200 = q.rolling(200).mean()
    # hysteresis: ON above SMA, OFF below 0.98*SMA (2% buffer to cut whipsaw)
    on = pd.Series(False, index=q.index)
    state = False
    for i in range(len(q)):
        if np.isnan(sma200.iloc[i]):
            on.iloc[i] = False; continue
        if not state and q.iloc[i] > sma200.iloc[i]:
            state = True
        elif state and q.iloc[i] < 0.98 * sma200.iloc[i]:
            state = False
        on.iloc[i] = state
    on = on.shift(1).fillna(False)

    # 60/30/10 leveraged blend, monthly rebal; when trend off -> cash
    blend = 0.60 * qr + 0.30 * qld_r + 0.10 * tqqq_r
    lev_trend = np.where(on, blend, cash_r)
    lev_trend = pd.Series(lev_trend, index=q.index) - on.astype(int).diff().abs().fillna(0) * 10 / 10_000.0

    # my core proxy: QQQ when 12mo-mom>0 else cash
    mom_on = (q / q.shift(252) - 1 > 0).shift(1).fillna(False)
    me = q.index.to_series().groupby(q.index.to_period("M")).transform("max") == q.index
    tgt = pd.Series(np.nan, index=q.index); tgt[me] = mom_on[me].astype(float).values
    tgt = tgt.ffill().fillna(0.0)
    core = tgt.shift(1).fillna(0.0) * qr + (1 - tgt.shift(1).fillna(0.0)) * cash_r \
        - tgt.diff().abs().fillna(0.0) * 5 / 10_000.0

    strategies = {
        "QQQ buy-hold": qr,
        "MY core (mom->cash)": core,
        "Tian 60/30/10 + SMA200 (trend)": lev_trend,
        "Tian 60/30/10 NO filter (buy-hold lev)": blend,
    }
    print(f"Tian leveraged test {q.index[0].date()} -> {q.index[-1].date()} (incl dot-com + GFC)\n")
    print(f"{'strategy':40s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s} {'$300k end':>14s}")
    for name, s in strategies.items():
        m = metrics(s)
        print(f"{name:40s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% "
              f"{m['w12mo']*100:6.1f}% {m['end']:>14,.0f}")
    print(f"\nSimulated QLD=2x, TQQQ=3x daily reset, expense {EXPENSE:.2%}+financing {FINANCE:.0%} on "
          f"borrow. Effective leverage ~1.5x. Raw-price (no dividends), pre-tax. Financing/decay "
          f"are the honesty knobs — leveraged-ETF drawdowns can gap below a monthly trend filter.")


if __name__ == "__main__":
    main()
