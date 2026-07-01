"""Experiment 18 — Close the AI-sleeve thread WITH taxes (the user's stated priority).

exp02/06 showed AI momentum improves the PRE-tax frontier but is survivorship-biased. Open
question: does it survive TAX? The AI sleeve rotates monthly -> short-term gains realized every
year (like options), while the QQQ core defers. Model each sleeve's proper after-tax and see if
a core+AI blend still beats the core after tax in a TAXABLE account.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
BASKET = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "AMD",
          "ADBE", "CRM", "ORCL", "QCOM", "TSLA", "NFLX"]
ROOT = Path(__file__).resolve().parents[2] / "data"
LTCG, ST = 0.238, 0.408


def me_mask(idx): return idx.to_series().groupby(idx.to_period("M")).transform("max") == idx


def stats(d):
    eq = (1 + d).cumprod()
    return (eq.iloc[-1] ** (TRADING_DAYS / len(d)) - 1, d.mean() / d.std() * np.sqrt(TRADING_DAYS),
            (eq / eq.cummax() - 1).min())


def deferred(d, rate=LTCG):
    end = 300_000 * (1 + d).cumprod().iloc[-1]; return end - max(end - 300_000, 0) * rate


def annual_st(d, rate=ST):
    eq = (1 + d).cumprod(); ye = eq.resample("YE").last(); prev, f = 1.0, 1.0
    for v in ye.values:
        g = v / prev - 1; f *= (1 + (g * (1 - rate) if g > 0 else g)); prev = v
    return 300_000 * f


def main():
    core = pd.read_csv(ROOT / "core_assets.csv", parse_dates=["Date"], index_col="Date").loc["2013":]
    bk = pd.read_csv(ROOT / "basket_adjclose.csv", parse_dates=["Date"], index_col="Date")
    names = [c for c in BASKET if c in bk.columns]
    q = core["QQQ"]
    on = (q / q.shift(252) - 1 > 0).shift(1).fillna(False)
    me = me_mask(q.index)
    tgt = pd.Series(np.nan, index=q.index); tgt[me] = on[me].astype(float).values
    tgt = tgt.ffill().fillna(0.0)
    core_r = (tgt.shift(1).fillna(0) * q.pct_change().fillna(0) + (1 - tgt.shift(1).fillna(0)) * core["BIL"].pct_change().fillna(0)
              - tgt.diff().abs().fillna(0) * 5 / 1e4).reindex(bk.index).fillna(0.0)

    mom = (bk[names] / bk[names].shift(126) - 1).shift(1)
    meb = me_mask(bk.index)
    w = pd.DataFrame(np.nan, index=bk.index, columns=names)
    for date in bk.index[meb]:
        row = pd.Series(0.0, index=names); cand = mom.loc[date].dropna(); cand = cand[cand > 0]
        row[cand.sort_values(ascending=False).head(5).index] = 1 / 5; w.loc[date] = row
    w = w.ffill().fillna(0.0)
    ai_r = (w.shift(1).fillna(0) * bk[names].pct_change().fillna(0)).sum(axis=1) - w.diff().abs().sum(axis=1).fillna(0) * 10 / 1e4

    print(f"AI sleeve after-tax {bk.index[0].date()} -> {bk.index[-1].date()} (survivorship-biased basket)\n")
    print(f"{'strategy':26s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>7s} {'pretax$':>11s} {'aftertax$':>11s}")
    qr = bk["QQQ"].pct_change().fillna(0.0)
    rows = [("QQQ buy-hold", qr, deferred), ("MY core", core_r, deferred), ("AI sleeve (rotates)", ai_r, annual_st)]
    for name, d, tax in rows:
        c, s, dd = stats(d); pre = 300_000 * (1 + d).cumprod().iloc[-1]
        print(f"{name:26s} {c*100:6.1f}% {s:7.2f} {dd*100:6.1f}% {pre:>11,.0f} {tax(d):>11,.0f}")
    # 80/20 after-tax = split the account (core deferred, AI annual-ST)
    for wai in (0.10, 0.20):
        blend = (1 - wai) * core_r + wai * ai_r
        c, s, dd = stats(blend); pre = 300_000 * (1 + blend).cumprod().iloc[-1]
        aftertax = (1 - wai) * deferred(core_r) + wai * annual_st(ai_r)
        print(f"{f'{int((1-wai)*100)}% core + {int(wai*100)}% AI':26s} {c*100:6.1f}% {s:7.2f} {dd*100:6.1f}% "
              f"{pre:>11,.0f} {aftertax:>11,.0f}")
    print("\nAI sleeve = monthly top-5 momentum (short-term gains, annual ST tax). Core/QQQ deferred. "
          "Survivorship-biased basket (today's winners) -> pre-tax already inflated; watch after-tax.")


if __name__ == "__main__":
    main()
