"""Experiment 15 — Stress-test my own winner: is the covered-call edge real or assumed?

Two honesty tests on the trend-gated covered call (exp14):
  A. IV SENSITIVITY: price the sold call at realized*{1.00,1.05,1.10,1.15}. The VRP edge is
     the sold-IV vs realized gap. At 1.00 (no VRP) the alpha should vanish -> shows how much
     of the 0.87 Sharpe is the VRP ASSUMPTION vs the trend structure.
  B. PROPER AFTER-TAX: buy-hold & core = DEFERRED LTCG (23.8% once at end); covered-call =
     annual short-term (30%). Does the CC still win after honest taxes in a TAXABLE account?
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


def stats(m, ppy=12):
    d = m.dropna(); eq = (1 + d).cumprod()
    return (eq.iloc[-1] ** (ppy / len(d)) - 1, d.mean() / d.std() * np.sqrt(ppy), (eq / eq.cummax() - 1).min())


def deferred_ltcg(m, rate=0.238):
    eq = (1 + m).cumprod(); end = 300_000 * eq.iloc[-1]
    return end - max(end - 300_000, 0) * rate


def annual_st(m, rate=0.30):
    eq = (1 + m).cumprod(); ye = eq.resample("YE").last(); prev, f = 1.0, 1.0
    for v in ye.values:
        g = v / prev - 1; f *= (1 + (g * (1 - rate) if g > 0 else g)); prev = v
    return 300_000 * f


def tgcc(m, mret, iv_mult, rvol_m, trend_on):
    out = []
    for i in range(1, len(m)):
        S, ret = m.iloc[i - 1], mret.iloc[i]
        sig = rvol_m.iloc[i - 1] * iv_mult
        if np.isnan(ret) or np.isnan(sig) or sig <= 0:
            out.append(0.0); continue
        prem = bs_call(S, S * 1.02, 1 / 12, sig) * (1 - SPREAD)
        out.append((min(ret, 0.02) + prem / S) if bool(trend_on.iloc[i]) else CASH / 12)
    return pd.Series(out, index=m.index[1:])


def main():
    q = pd.read_csv(ROOT / "qqq_daily.csv", parse_dates=["Date"], index_col="Date")["Close"]
    rvol_m = (q.pct_change().rolling(21).std() * np.sqrt(252)).resample("ME").last().clip(0.12, 0.60)
    m = q.resample("ME").last(); mret = m.pct_change()
    trend_on = (q / q.shift(252) - 1 > 0).resample("ME").last().shift(1).fillna(False)
    idx = m.index[1:]
    qqq_m = mret.reindex(idx).fillna(0.0)
    core = pd.Series(np.where(trend_on.reindex(idx).fillna(False), qqq_m, CASH / 12), index=idx)

    print("A. IV SENSITIVITY — trend-gated covered call (1999-2026)")
    print(f"   {'sold IV':12s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s}")
    for mult in (1.00, 1.05, 1.10, 1.15):
        c, s, dd = stats(tgcc(m, mret, mult, rvol_m, trend_on))
        print(f"   realized*{mult:.2f} {c*100:6.1f}% {s:7.2f} {dd*100:7.1f}%")

    print("\nB. PROPER AFTER-TAX (taxable): buy-hold/core DEFERRED LTCG; covered-call annual ST")
    cc = tgcc(m, mret, 1.10, rvol_m, trend_on)
    rows = [("QQQ buy-hold", qqq_m, deferred_ltcg), ("MY core (trend->cash)", core, deferred_ltcg),
            ("Trend-gated covered-call", cc, annual_st)]
    print(f"   {'strategy':28s} {'pretax$':>11s} {'aftertax$':>11s}")
    for name, s, taxfn in rows:
        eq = (1 + s).cumprod(); pre = 300_000 * eq.iloc[-1]
        print(f"   {name:28s} {pre:>11,.0f} {taxfn(s):>11,.0f}")
    print("\nRead A: if the edge mostly needs IV>=1.10, it's VRP-assumption-driven. Read B: does CC's "
          "short-term-tax drag give up its edge vs deferred buy-hold?")


if __name__ == "__main__":
    main()
