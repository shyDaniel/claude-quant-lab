"""Experiment 16 — Bootstrap significance of the trend-gated covered call (keep breaking it).

exp09 bootstrapped the CORE and forced me to withdraw the 'beats QQQ on Sharpe' claim (noise).
Apply the same skepticism to my IRA winner: block-bootstrap monthly returns; in what fraction
of alternate histories does the trend-gated covered call beat QQQ / the core on Sharpe, and
have a shallower drawdown? High % = robust; ~50% = luck.
"""

from __future__ import annotations

from math import erf, exp, log, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "data"
R, CASH, SPREAD = 0.02, 0.02, 0.01
BLOCK, N = 6, 5000


def ncdf(x): return 0.5 * (1 + erf(x / sqrt(2)))
def bs_call(S, K, T, sig):
    if T <= 0 or sig <= 0: return max(S - K, 0)
    d1 = (log(S / K) + (R + 0.5 * sig ** 2) * T) / (sig * sqrt(T)); return S * ncdf(d1) - K * exp(-R * T) * ncdf(d1 - sig * sqrt(T))


def sharpe(x): return x.mean() / x.std() * np.sqrt(12)
def maxdd(x):
    eq = np.cumprod(1 + x); return float((eq / np.maximum.accumulate(eq) - 1).min())


def boot(a, b, la, lb):
    rng = np.random.default_rng(7); T = len(a); nb = T // BLOCK + 1
    sd, wdd = [], 0
    for _ in range(N):
        starts = rng.integers(0, T - BLOCK, nb)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:T]
        sa, sb = a[idx], b[idx]
        sd.append(sharpe(sa) - sharpe(sb)); wdd += maxdd(sa) > maxdd(sb)
    sd = np.array(sd)
    print(f"  {la} vs {lb}: P(Sharpe {la}>{lb})={np.mean(sd>0)*100:4.1f}%  "
          f"90%CI[{np.percentile(sd,5):+.2f},{np.percentile(sd,95):+.2f}]  "
          f"P(shallower DD)={wdd/N*100:4.1f}%")


def main():
    q = pd.read_csv(ROOT / "qqq_daily.csv", parse_dates=["Date"], index_col="Date")["Close"]
    rvol_m = (q.pct_change().rolling(21).std() * np.sqrt(252)).resample("ME").last().clip(0.12, 0.60)
    m = q.resample("ME").last(); mret = m.pct_change()
    trend_on = (q / q.shift(252) - 1 > 0).resample("ME").last().shift(1).fillna(False)
    cc = []
    for i in range(1, len(m)):
        S, ret, sig = m.iloc[i - 1], mret.iloc[i], rvol_m.iloc[i - 1] * 1.10
        if np.isnan(ret) or np.isnan(sig) or sig <= 0: cc.append(0.0); continue
        prem = bs_call(S, S * 1.02, 1 / 12, sig) * (1 - SPREAD)
        cc.append((min(ret, 0.02) + prem / S) if bool(trend_on.iloc[i]) else CASH / 12)
    idx = m.index[1:]
    ccv = np.array(cc)
    qv = mret.reindex(idx).fillna(0.0).values
    corev = np.where(trend_on.reindex(idx).fillna(False).values, qv, CASH / 12)
    print(f"Bootstrap (N={N}, block={BLOCK}mo) {idx[0].date()} -> {idx[-1].date()}")
    boot(ccv, qv, "CC", "QQQ")
    boot(ccv, corev, "CC", "core")
    print("Read: >80% = robust edge; ~50% or CI spans 0 = within noise (be honest).")


if __name__ == "__main__":
    main()
