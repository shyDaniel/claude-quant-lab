"""Experiment 13 — Volatility risk premium: sell QQQ options (Tian's real gem).

Option SELLERS get paid for the same IV-overpricing that makes BUYING LEAPS bad. Test
systematic monthly premium-selling on QQQ, honestly, over 1999-2026 (so the 2008/2020
crash risk of premium-selling shows up). Price sold options at IV = trailing realized*1.10
(the VRP source); payoff uses ACTUAL monthly moves. Net of option spread. vs QQQ + my core.
  - Covered call: own QQQ, sell ~2% OTM 1-mo call (cap upside, keep premium).
  - Put-write: cash + sell ATM 1-mo put (income, full downside beyond premium).
"""

from __future__ import annotations

from math import erf, exp, log, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
ROOT = Path(__file__).resolve().parents[2] / "data"
R, CASH = 0.02, 0.02
SPREAD = 0.01   # 1% of premium as round-trip friction


def ncdf(x):
    return 0.5 * (1 + erf(x / sqrt(2)))


def bs(S, K, T, sig, call=True):
    if T <= 0 or sig <= 0:
        return max(S - K, 0) if call else max(K - S, 0)
    d1 = (log(S / K) + (R + 0.5 * sig ** 2) * T) / (sig * sqrt(T))
    d2 = d1 - sig * sqrt(T)
    if call:
        return S * ncdf(d1) - K * exp(-R * T) * ncdf(d2)
    return K * exp(-R * T) * ncdf(-d2) - S * ncdf(-d1)


def metrics(monthly, ppy=12):
    d = monthly.dropna()
    eq = (1 + d).cumprod()
    return {"CAGR": eq.iloc[-1] ** (ppy / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(ppy),
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(ppy).min()}


def main():
    df = pd.read_csv(ROOT / "qqq_daily.csv", parse_dates=["Date"], index_col="Date")
    q = df["Close"]
    qr_d = q.pct_change()
    rvol = qr_d.rolling(21).std() * np.sqrt(TRADING_DAYS)     # trailing realized vol
    m = q.resample("ME").last()
    mret = m.pct_change()
    iv = (rvol.resample("ME").last() * 1.10).clip(0.12, 0.60)  # sold IV carries the VRP
    T = 1 / 12

    cc, pw = [], []
    for i in range(1, len(m)):
        S = m.iloc[i - 1]
        ret = mret.iloc[i]
        sig = iv.iloc[i - 1]
        if np.isnan(ret) or np.isnan(sig):
            cc.append(0.0); pw.append(0.0); continue
        # covered call: 2% OTM call
        Kc = S * 1.02
        prem_c = bs(S, Kc, T, sig, call=True) * (1 - SPREAD)
        cc_ret = min(ret, 0.02) + prem_c / S                  # capped upside + premium, full downside
        cc.append(cc_ret)
        # put-write: ATM put, cash-collateralized
        Kp = S
        prem_p = bs(S, Kp, T, sig, call=False) * (1 - SPREAD)
        payoff = prem_p - max(0.0, Kp - S * (1 + ret))        # lose if QQQ falls below strike
        pw.append(payoff / S + CASH / 12)
        cc_idx = m.index[1:]
    cc = pd.Series(cc, index=m.index[1:])
    pw = pd.Series(pw, index=m.index[1:])
    qqq_m = mret.dropna()

    print(f"VRP overlay (monthly) {m.index[0].date()} -> {m.index[-1].date()} | 1999-2026\n")
    print(f"{'strategy':28s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s}")
    for name, s in {"QQQ buy-hold (monthly)": qqq_m,
                    "Covered-call (2% OTM)": cc,
                    "Put-write (ATM)": pw,
                    "Half QQQ + half put-write": 0.5 * qqq_m.reindex(pw.index).fillna(0) + 0.5 * pw}.items():
        mt = metrics(s)
        print(f"{name:28s} {mt['CAGR']*100:6.1f}% {mt['Sharpe']:7.2f} {mt['MaxDD']*100:7.1f}% {mt['w12mo']*100:6.1f}%")
    print("\nSold IV = trailing realized*1.10 (VRP); payoff = actual monthly move. Monthly, net 1% "
          "spread. Negative skew: watch 2000/2008/2020 drawdowns. Pre-tax (premium = short-term).")


if __name__ == "__main__":
    main()
