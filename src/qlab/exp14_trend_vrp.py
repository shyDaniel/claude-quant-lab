"""Experiment 14 — THE SYNTHESIS: trend-gated covered call (VRP + drawdown control).

exp13 showed a covered-call overlay harvests the VRP (Sharpe 0.82) but still owns QQQ in
crashes (-57% DD). exp04 showed the trend filter halves drawdown. Combine them: sell covered
calls on QQQ ONLY when the trend is ON; sit in cash (T-bills) when OFF. Target = the VRP's
Sharpe edge + the core's ~-29% drawdown. Also reports after-tax (premium is short-term) since
that decides taxable vs IRA. Beats what Codex only *planned* (DCA_PUT_ENTRY) by actually running it.
"""

from __future__ import annotations

from math import erf, exp, log, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "data"
R, CASH, SPREAD = 0.02, 0.02, 0.01


def ncdf(x): return 0.5 * (1 + erf(x / sqrt(2)))
def bs_call(S, K, T, sig):
    if T <= 0 or sig <= 0: return max(S - K, 0)
    d1 = (log(S / K) + (R + 0.5 * sig ** 2) * T) / (sig * sqrt(T)); return S * ncdf(d1) - K * exp(-R * T) * ncdf(d1 - sig * sqrt(T))


def metrics(monthly, ppy=12):
    d = monthly.dropna(); eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (ppy / len(d)) - 1, "Sharpe": d.mean() / d.std() * np.sqrt(ppy),
            "MaxDD": (eq / eq.cummax() - 1).min(), "w12mo": eq.pct_change(ppy).min(),
            "aftertax_end": aftertax(d)}


def aftertax(monthly, rate=0.30):
    """Annual realization of gains at 30% blended (premium is short-term). Approx."""
    eq = (1 + monthly).cumprod()
    ye = eq.resample("YE").last(); prev, f = 1.0, 1.0
    for v in ye.values:
        g = v / prev - 1; f *= (1 + (g * (1 - rate) if g > 0 else g)); prev = v
    return 300_000 * f


def main():
    df = pd.read_csv(ROOT / "qqq_daily.csv", parse_dates=["Date"], index_col="Date")
    q = df["Close"]; qr_d = q.pct_change()
    rvol = qr_d.rolling(21).std() * np.sqrt(252)
    mom_on_d = (q / q.shift(252) - 1 > 0)                       # 12-mo trend, daily
    m = q.resample("ME").last(); mret = m.pct_change()
    iv = (rvol.resample("ME").last() * 1.10).clip(0.12, 0.60)
    trend_on = mom_on_d.resample("ME").last().shift(1).fillna(False)  # trend as of prior month-end

    cc = []          # pure covered call (exp13)
    tcc = []         # trend-gated covered call
    for i in range(1, len(m)):
        S, ret, sig = m.iloc[i - 1], mret.iloc[i], iv.iloc[i - 1]
        if np.isnan(ret) or np.isnan(sig):
            cc.append(0.0); tcc.append(0.0); continue
        prem = bs_call(S, S * 1.02, 1 / 12, sig) * (1 - SPREAD)
        cc_ret = min(ret, 0.02) + prem / S
        cc.append(cc_ret)
        tcc.append(cc_ret if bool(trend_on.iloc[i]) else CASH / 12)  # cash when trend off
    idx = m.index[1:]
    cc = pd.Series(cc, index=idx); tcc = pd.Series(tcc, index=idx)
    qqq_m = mret.reindex(idx).fillna(0.0)
    core = pd.Series(np.where(trend_on.reindex(idx).fillna(False), qqq_m, CASH / 12), index=idx)

    print(f"Trend-gated VRP synthesis {idx[0].date()} -> {idx[-1].date()} | 1999-2026\n")
    print(f"{'strategy':30s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s} {'aftertax$':>11s}")
    for name, s in {"QQQ buy-hold": qqq_m, "MY core (trend->cash)": core,
                    "Covered-call (no gate)": cc, "TREND-GATED covered-call": tcc}.items():
        mt = metrics(s)
        print(f"{name:30s} {mt['CAGR']*100:6.1f}% {mt['Sharpe']:7.2f} {mt['MaxDD']*100:7.1f}% "
              f"{mt['w12mo']*100:6.1f}% {mt['aftertax_end']:>11,.0f}")
    print("\nMonthly, sold IV=realized*1.10, 1% spread. After-tax = annual realization @30% (premium "
          "short-term). Trend-gated CC aims for VRP Sharpe + core drawdown.")


if __name__ == "__main__":
    main()
