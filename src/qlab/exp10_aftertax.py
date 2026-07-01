"""Experiment 10 — After-tax dollars: does LEAPS's raw-$ edge survive taxes?

The head-to-head (exp08) was pre-tax. LEAPS is tax-ugly: rolled ~annually + trend-exits =
gains realized short-term, every year. Buy-hold defers ALL gains (LTCG once at the end).
Trend rules are low-turnover (hold QQQ for years) => mostly deferred/long-term. Model each
honestly and re-rank by after-tax $300k terminal wealth.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp08_leaps_headtohead import month_end, simulate_leaps  # noqa: E402

TRADING_DAYS = 252
ROOT = Path(__file__).resolve().parents[2] / "data"
LTCG, BLEND_ST = 0.238, 0.32   # long-term cap-gains; blended short/long for options


def deferred_ltcg(nav: pd.Series, rate: float = LTCG) -> float:
    """Defer all gains, pay LTCG once at liquidation (buy-hold & low-turnover trend)."""
    gain = nav.iloc[-1] - nav.iloc[0]
    return float(nav.iloc[-1] - max(gain, 0.0) * rate)


def annual_realized(nav: pd.Series, rate: float) -> float:
    """Realize + tax gains every calendar year (LEAPS rolls) -> compounding tax drag."""
    ye = nav.resample("YE").last()
    prev, factor = nav.iloc[0], 1.0
    for v in ye.values:
        g = v / prev - 1.0
        factor *= (1 + (g * (1 - rate) if g > 0 else g))
        prev = v
    return float(nav.iloc[0] * factor)


def core_nav(px: pd.DataFrame, off: str) -> pd.Series:
    q = px["QQQ"]
    on = (q / q.shift(252) - 1 > 0).shift(1).fillna(False)
    me = month_end(q.index)
    tgt = pd.Series(np.nan, index=q.index)
    tgt[me] = on[me].astype(float).values
    tgt = tgt.ffill().fillna(0.0)
    w = tgt.shift(1).fillna(0.0)
    r = w * q.pct_change().fillna(0.0) + (1 - w) * px[off].pct_change().fillna(0.0) \
        - tgt.diff().abs().fillna(0.0) * 5 / 10_000.0
    return (1 + r).cumprod()


def main() -> None:
    px = pd.read_csv(ROOT / "core_assets.csv", parse_dates=["Date"], index_col="Date").loc["2007":]
    q, bil_r = px["QQQ"], px["BIL"].pct_change().fillna(0.0)
    trend_on = (q / q.shift(252) - 1 > 0).shift(1).fillna(False)

    navs = {
        "QQQ buy-hold": ((1 + q.pct_change().fillna(0.0)).cumprod(), "deferred"),
        "MY core (mom->T-bills)": (core_nav(px, "BIL"), "deferred"),
        "Codex core (mom->IEF)": (core_nav(px, "IEF"), "deferred"),
        "LEAPS gated 55% (IV22)": (simulate_leaps(q, bil_r, trend_on, 0.22, 0.55, True), "annual"),
        "LEAPS ungated 55%": (simulate_leaps(q, bil_r, trend_on, 0.22, 0.55, False), "annual"),
    }
    print(f"After-tax head-to-head {px.index[0].date()} -> {px.index[-1].date()} | $300k start\n")
    print(f"{'strategy':30s} {'pre-tax $':>12s} {'after-tax $':>12s} {'tax drag':>9s} {'treatment':>10s}")
    for name, (nav, treat) in navs.items():
        pre = 300_000 * nav.iloc[-1] / nav.iloc[0]
        aft = 300_000 * (deferred_ltcg(nav) if treat == "deferred" else annual_realized(nav, BLEND_ST)) / nav.iloc[0]
        print(f"{name:30s} {pre:>12,.0f} {aft:>12,.0f} {(1-aft/pre)*100:8.1f}% {treat:>10s}")
    print("\nDeferred = LTCG 23.8% once at end (buy-hold + low-turnover trend). Annual = realize "
          "+ tax 32% blended each year (LEAPS rolls short-term). Approx; real tax varies by bracket/account.")


if __name__ == "__main__":
    main()
