"""Experiment 17 — Can Section 1256 (index options) rescue premium-selling in TAXABLE?

exp15 killed the covered call in taxable (monthly short-term premium). The pro fix: use
options on the INDEX (NDX/XND), which are Section 1256 contracts -> 60% long-term / 40%
short-term blended rate regardless of holding period. Test whether 1256 treatment makes the
trend-gated premium strategy beat buy-hold QQQ after tax in a taxable account. Honest prior:
1256 lowers the RATE, but premium is still realized ANNUALLY (no deferral) -> buy-hold's
decades of deferral likely still win. Verify the magnitude.
"""

from __future__ import annotations

from math import erf, exp, log, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "data"
R, CASH, SPREAD = 0.02, 0.02, 0.01
LTCG, ST = 0.238, 0.408                 # incl 3.8% NIIT
BLEND_1256 = 0.6 * LTCG + 0.4 * ST      # ~0.306


def ncdf(x): return 0.5 * (1 + erf(x / sqrt(2)))
def bs_call(S, K, T, sig):
    if T <= 0 or sig <= 0: return max(S - K, 0)
    d1 = (log(S / K) + (R + 0.5 * sig ** 2) * T) / (sig * sqrt(T)); return S * ncdf(d1) - K * exp(-R * T) * ncdf(d1 - sig * sqrt(T))


def deferred(m, rate=LTCG):
    end = 300_000 * (1 + m).cumprod().iloc[-1]; return end - max(end - 300_000, 0) * rate


def annual(m, rate):
    eq = (1 + m).cumprod(); ye = eq.resample("YE").last(); prev, f = 1.0, 1.0
    for v in ye.values:
        g = v / prev - 1; f *= (1 + (g * (1 - rate) if g > 0 else g)); prev = v
    return 300_000 * f


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
    idx = m.index[1:]; cc = pd.Series(cc, index=idx)
    qqq_m = mret.reindex(idx).fillna(0.0)
    pre = 300_000 * (1 + cc).cumprod().iloc[-1]
    qpre = 300_000 * (1 + qqq_m).cumprod().iloc[-1]

    print(f"Section 1256 taxable test {idx[0].date()} -> {idx[-1].date()}\n")
    print(f"  Buy-hold QQQ  : pre-tax ${qpre:,.0f} -> after-tax (deferred LTCG) ${deferred(qqq_m):,.0f}")
    print(f"  Covered call  : pre-tax ${pre:,.0f}")
    print(f"    - equity options (annual ST {ST:.1%}):     after-tax ${annual(cc, ST):,.0f}")
    print(f"    - Section 1256 (annual 60/40 {BLEND_1256:.1%}): after-tax ${annual(cc, BLEND_1256):,.0f}")
    print(f"    - [hypothetical] if it could DEFER at LTCG: ${deferred(cc):,.0f}")
    print("\nVerdict: does 1256 (index options) let premium-selling beat buy-hold after tax in "
          "taxable? The gap between 'annual 1256' and 'deferred' shows deferral, not the rate, is "
          "the real moat.")


if __name__ == "__main__":
    main()
