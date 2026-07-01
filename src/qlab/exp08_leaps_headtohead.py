"""Experiment 08 — Head-to-head: my core vs Codex core vs LEAPS vs QQQ. All data, all $.

The user can execute LEAPS, so model it honestly (Black-Scholes, deep-ITM, realistic
spread + IV) and put every candidate on ONE board: risk (drawdown, worst-12mo, vol) and
return (CAGR, $300k ending value), 2007-2026, net of costs. No hand-waving.
"""

from __future__ import annotations

from math import erf, exp, log, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
ROOT = Path(__file__).resolve().parents[2] / "data"
R = 0.03  # risk-free for BS


def ncdf(x: float) -> float:
    return 0.5 * (1 + erf(x / sqrt(2)))


def bs_call(S: float, K: float, T: float, sigma: float) -> float:
    if T <= 1e-6:
        return max(S - K, 0.0)
    d1 = (log(S / K) + (R + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    return S * ncdf(d1) - K * exp(-R * T) * ncdf(d1 - sigma * sqrt(T))


def metrics(nav: pd.Series) -> dict[str, float]:
    d = nav.pct_change().dropna()
    eq = nav / nav.iloc[0]
    return {"CAGR": eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1,
            "Sharpe": d.mean() / d.std() * np.sqrt(TRADING_DAYS),
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "w12mo": eq.pct_change(TRADING_DAYS).min(),
            "end": 300_000 * eq.iloc[-1]}


def month_end(idx: pd.DatetimeIndex) -> np.ndarray:
    return (idx.to_series().groupby(idx.to_period("M")).transform("max") == idx).values


def simulate_leaps(spot: pd.Series, bil: pd.Series, trend_on: pd.Series,
                   iv: float, prem_w: float, gated: bool, spread: float = 0.02,
                   moneyness: float = 0.80, life_days: int = 504, roll_days: int = 252) -> pd.Series:
    idx = spot.index
    me = month_end(idx)
    cash, contracts, K, exp_i = 1.0, 0.0, None, None
    navs = np.empty(len(idx))
    for i in range(len(idx)):
        S = float(spot.iloc[i])
        if i > 0:
            cash *= (1 + float(bil.iloc[i]))
        opt = bs_call(S, K, (exp_i - i) / TRADING_DAYS, iv) if contracts > 0 else 0.0
        nav = cash + contracts * opt
        if me[i]:
            want_on = (not gated) or bool(trend_on.iloc[i])
            need_roll = contracts > 0 and (exp_i - i) <= roll_days
            if contracts > 0 and (not want_on or need_roll):        # close
                cash += contracts * opt * (1 - spread)
                contracts, K, exp_i = 0.0, None, None
                nav = cash
            if want_on and contracts == 0 and i < len(idx) - 1:      # open deep-ITM LEAPS
                K = S * moneyness
                price = bs_call(S, K, life_days / TRADING_DAYS, iv)
                target = prem_w * nav
                contracts = target / (price * (1 + spread))
                cash = nav - contracts * price * (1 + spread)
                exp_i = i + life_days
        navs[i] = nav
    return pd.Series(navs, index=idx)


def main() -> None:
    px = pd.read_csv(ROOT / "core_assets.csv", parse_dates=["Date"], index_col="Date").loc["2007":]
    qqq, bil = px["QQQ"], px["BIL"]
    bil_r = bil.pct_change().fillna(0.0)
    trend_on = (qqq / qqq.shift(252) - 1 > 0).shift(1).fillna(False)

    def core_nav(off: str) -> pd.Series:              # my core / Codex core proxy
        me = month_end(qqq.index)
        tgt = pd.Series(np.nan, index=qqq.index)
        tgt[me] = trend_on[me].astype(float).values
        tgt = tgt.ffill().fillna(0.0)
        w = tgt.shift(1).fillna(0.0)
        r = w * qqq.pct_change().fillna(0.0) + (1 - w) * (px[off].pct_change().fillna(0.0)) \
            - tgt.diff().abs().fillna(0.0) * 5 / 10_000.0
        return 300_000 / 300_000 * (1 + r).cumprod()

    board = {
        "QQQ buy-hold": (1 + qqq.pct_change().fillna(0.0)).cumprod(),
        "MY core (12mo-mom->T-bills)": core_nav("BIL"),
        "Codex core (mom->IEF)": core_nav("IEF"),
        "LEAPS gated (prem 40%, IV22)": simulate_leaps(qqq, bil_r, trend_on, 0.22, 0.40, True),
        "LEAPS gated (prem 55%, IV22)": simulate_leaps(qqq, bil_r, trend_on, 0.22, 0.55, True),
        "LEAPS ungated (prem 55%, IV22)": simulate_leaps(qqq, bil_r, trend_on, 0.22, 0.55, False),
        "LEAPS gated conservative (IV25)": simulate_leaps(qqq, bil_r, trend_on, 0.25, 0.40, True, spread=0.03),
    }
    print(f"Head-to-head {px.index[0].date()} -> {px.index[-1].date()} | $300k start, net of costs\n")
    print(f"{'strategy':34s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>8s} {'w12mo':>7s} {'$300k end':>13s}")
    for name, nav in board.items():
        m = metrics(nav)
        print(f"{name:34s} {m['CAGR']*100:6.1f}% {m['Sharpe']:7.2f} {m['MaxDD']*100:7.1f}% "
              f"{m['w12mo']*100:6.1f}% {m['end']:>13,.0f}")
    print("\nLEAPS = synthetic Black-Scholes (deep-ITM 0.8-delta, 2yr, roll@1yr, 2-3% spread, "
          "IV 22-25%, no tax). Real fills/IV/tax will be worse. Gated = hold only when QQQ 12mo-mom>0.")


if __name__ == "__main__":
    main()
