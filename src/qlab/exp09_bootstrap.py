"""Experiment 09 — Is the edge REAL or luck? Block-bootstrap significance.

The deepest 'proof' rung: resample the joint daily returns (block bootstrap, preserves
autocorrelation) thousands of times and ask, in what fraction of alternate histories does
the core rule still (a) beat QQQ's Sharpe and (b) have a shallower drawdown? High fractions
=> the edge is statistically robust, not a single lucky path. Also tests my core vs Codex's
core (expected: statistical tie = same strategy family).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
BLOCK = 63          # ~quarter, preserves trend/autocorrelation
N = 5000
ROOT = Path(__file__).resolve().parents[2] / "data"


def core_daily(px: pd.DataFrame, off: str) -> pd.Series:
    q = px["QQQ"]
    on = (q / q.shift(252) - 1 > 0).shift(1).fillna(False)
    me = q.index.to_series().groupby(q.index.to_period("M")).transform("max") == q.index
    tgt = pd.Series(np.nan, index=q.index)
    tgt[me] = on[me].astype(float).values
    tgt = tgt.ffill().fillna(0.0)
    w = tgt.shift(1).fillna(0.0)
    return w * q.pct_change().fillna(0.0) + (1 - w) * px[off].pct_change().fillna(0.0) \
        - tgt.diff().abs().fillna(0.0) * 5 / 10_000.0


def sharpe(x: np.ndarray) -> float:
    return x.mean() / x.std() * np.sqrt(TRADING_DAYS)


def maxdd(x: np.ndarray) -> float:
    eq = np.cumprod(1 + x)
    return float((eq / np.maximum.accumulate(eq) - 1).min())


def bootstrap(a: np.ndarray, b: np.ndarray, label_a: str, label_b: str) -> None:
    rng = np.random.default_rng(42)
    T = len(a)
    n_blocks = T // BLOCK + 1
    sh_diff, dd_a, dd_b, win_dd = [], [], [], 0
    for _ in range(N):
        starts = rng.integers(0, T - BLOCK, n_blocks)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:T]
        sa, sb = a[idx], b[idx]
        sh_diff.append(sharpe(sa) - sharpe(sb))
        da, db = maxdd(sa), maxdd(sb)
        dd_a.append(da); dd_b.append(db)
        win_dd += da > db          # a shallower (less negative) drawdown
    sh_diff = np.array(sh_diff)
    print(f"\n{label_a} vs {label_b}  (N={N} block-bootstraps, block={BLOCK}d)")
    print(f"  P({label_a} Sharpe > {label_b}) = {(sh_diff > 0).mean()*100:5.1f}%")
    print(f"  Sharpe diff: mean {sh_diff.mean():+.3f}, 90% CI [{np.percentile(sh_diff,5):+.3f}, "
          f"{np.percentile(sh_diff,95):+.3f}]")
    print(f"  P({label_a} shallower drawdown) = {win_dd/N*100:5.1f}%")
    print(f"  median MaxDD: {label_a} {np.median(dd_a)*100:5.1f}%  vs  {label_b} {np.median(dd_b)*100:5.1f}%")


def main() -> None:
    px = pd.read_csv(ROOT / "core_assets.csv", parse_dates=["Date"], index_col="Date").loc["2007":]
    df = pd.concat([core_daily(px, "BIL").rename("core"),
                    px["QQQ"].pct_change().rename("qqq"),
                    core_daily(px, "IEF").rename("codex")], axis=1).dropna()
    print(f"Bootstrap significance, {df.index[0].date()} -> {df.index[-1].date()}")
    bootstrap(df["core"].values, df["qqq"].values, "MY core", "QQQ")
    bootstrap(df["core"].values, df["codex"].values, "MY core", "Codex core")
    print("\nRead: >~80% = robust edge; ~50% = statistical tie (luck-indistinguishable).")


if __name__ == "__main__":
    main()
