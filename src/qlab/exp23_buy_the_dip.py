"""Exp23 — does "buy the dip" actually help? (The thing the user is doing today.)
Two honest framings the user cares about:
  (A) Deploying idle cash: lump-sum NOW vs. holding cash and buying only on X% dips (QQQ, 10y).
  (B) A dip-buying rule (own what's WEAK) vs. buy-and-hold vs. buy-strength (own what's STRONG),
      monthly, on BOTH QQQ and the AI-capex basket.

CAVEATS as exp19/21: AI basket = survivorship + ~3yr single regime; several variants tested
(overfitting risk). Requires live data — Yahoo is blocked in the cloud sandbox; run LOCALLY.
"""
from __future__ import annotations
import yfinance as yf, numpy as np, pandas as pd

BASKET = ["NVDA","AMD","AVGO","MU","SNDK","MRVL","STX","ANET","VST","CEG","GEV","VRT","NBIS"]


def stats(r):
    r = r.dropna(); eq = (1 + r).cumprod()
    return (eq.iloc[-1] ** (252 / len(r)) - 1,
            r.mean() / r.std() * np.sqrt(252),
            (eq / eq.cummax() - 1).min())


def deploy_on_dips(ret, dd_trigger=0.10, tranches=5):
    """Hold cash; deploy one tranche (1/tranches) each time drawdown from the prior peak
    crosses another -dd_trigger step. Illustrative cash-timing test vs. investing all now."""
    px = (1 + ret.fillna(0)).cumprod()
    dd = px / px.cummax() - 1
    w, used = 0.0, 0
    weight = pd.Series(0.0, index=px.index)
    for t in px.index:
        step = int((-dd.loc[t]) // dd_trigger)
        if step > used and w < 1.0:
            add = min(step - used, tranches - used)
            w = min(1.0, w + add / tranches); used += add
        weight.loc[t] = w
    return weight.shift(1).fillna(0.0) * ret


def monthly_rule(px, pick):
    """pick = boolean signal (Series for one asset, DataFrame for a universe). Rebalance monthly,
    equal-weight the picks, apply next day (shift) to avoid look-ahead."""
    me = px.index.to_series().groupby(px.index.to_period("M")).transform("max") == px.index
    sig = pick.shift(1)
    if isinstance(px, pd.Series):
        w = pd.Series(np.nan, index=px.index)
        for t in px.index[me]:
            w.loc[t] = 1.0 if bool(sig.loc[t]) else 0.0
        return w.ffill().fillna(0.0).shift(1) * px.pct_change()
    w = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
    for t in px.index[me]:
        on = sig.loc[t].fillna(False); n = int(on.sum())
        w.loc[t] = on.astype(float) / n if n else 0.0
    return (w.ffill().fillna(0.0).shift(1) * px.pct_change()).sum(axis=1)


def main():
    # ---- (A) $100k cash into QQQ: lump-sum vs. buy-the-dip deployment ----
    qpx = yf.download("QQQ", period="10y", auto_adjust=True, progress=False)["Close"].dropna()
    qret = qpx.pct_change()
    print("== (A) Deploying idle cash into QQQ (10y) ==")
    for name, r in [("lump sum (invest all now)", qret),
                    ("wait & buy -10% dips (5 tranches)", deploy_on_dips(qret, 0.10, 5)),
                    ("wait & buy -5% dips (5 tranches)",  deploy_on_dips(qret, 0.05, 5))]:
        c, s, d = stats(r)
        print(f"  {name:34s} CAGR {c*100:5.1f}%  Sharpe {s:.2f}  MaxDD {d*100:.0f}%")

    # ---- (B) dip (own weakness) vs hold vs strength (own strength) ----
    ma_q = qpx.rolling(100).mean()
    print("\n== (B) QQQ: dip vs hold vs strength (monthly, 10y) ==")
    for name, r in [("buy & hold", qret),
                    ("buy the dip (below 100d)",  monthly_rule(qpx, qpx < ma_q)),
                    ("buy strength (above 100d)", monthly_rule(qpx, qpx > ma_q))]:
        c, s, d = stats(r)
        print(f"  {name:30s} CAGR {c*100:5.1f}%  Sharpe {s:.2f}  MaxDD {d*100:.0f}%")

    bpx = yf.download(BASKET, period="3y", auto_adjust=True,
                      progress=False)["Close"].dropna(how="all")
    ma_b = bpx.rolling(100).mean()
    print("\n== (B) AI-capex basket: dip vs hold vs strength (monthly, ~3y) ==")
    for name, r in [("buy & hold (equal weight)", bpx.pct_change().mean(axis=1)),
                    ("buy the dip (below 100d)",  monthly_rule(bpx, bpx < ma_b)),
                    ("buy strength (above 100d)", monthly_rule(bpx, bpx > ma_b))]:
        c, s, d = stats(r)
        print(f"  {name:30s} CAGR {c*100:5.1f}%  Sharpe {s:.2f}  MaxDD {d*100:.0f}%")

    print("\nCAVEAT: AI basket survivorship + one regime; many variants tested. See DUE_DILIGENCE.md.")


if __name__ == "__main__":
    main()
