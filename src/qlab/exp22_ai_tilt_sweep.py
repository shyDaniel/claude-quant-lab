"""Exp22 — "less QQQ, more AI": allocation sweep of QQQ vs a trend-gated AI-capex basket.
Directly answers the user's ask: what happens to CAGR / Sharpe / drawdown as you shift weight
OUT of QQQ and INTO the AI sleeve, with and without the 100-day crash switch.

CAVEATS (critical — read before trusting any number):
  * The AI basket is 2026's KNOWN WINNERS (survivorship bias) over a ~3-year SINGLE REGIME
    (the 2023-2026 AI-capex + memory supercycle) with NO in-sample bear market. The returns
    are a THESIS ILLUSTRATION, not forward estimates. See outputs/DUE_DILIGENCE.md.
  * Memory/semis are the most cyclical corner of tech (historical -50% to -70% crashes).
Requires live data (yfinance/Yahoo). Yahoo is blocked by the cloud sandbox egress policy —
run this LOCALLY.
"""
from __future__ import annotations
import yfinance as yf, numpy as np, pandas as pd

BASKET = ["NVDA","AMD","AVGO","MU","SNDK","MRVL","STX","ANET","VST","CEG","GEV","VRT","NBIS"]


def stats(r):
    r = r.dropna(); eq = (1 + r).cumprod()
    cagr = eq.iloc[-1] ** (252 / len(r)) - 1
    sharpe = r.mean() / r.std() * np.sqrt(252)
    maxdd = (eq / eq.cummax() - 1).min()
    w12 = eq.pct_change(252).min()          # worst rolling 12-month
    return cagr, sharpe, maxdd, w12


def main():
    px = yf.download(BASKET + ["QQQ"], period="3y", auto_adjust=True,
                     progress=False)["Close"].dropna(how="all")
    qqq = px["QQQ"].pct_change()
    ew = px[BASKET].pct_change().mean(axis=1)                 # equal-weight AI basket
    nav = (1 + ew.fillna(0)).cumprod()
    gate = (nav > nav.rolling(100).mean()).shift(1).fillna(False)   # basket 100d crash switch
    ai_gated = pd.Series(np.where(gate, ew, 0.0), index=px.index)   # AI sleeve WITH the exit

    hdr = f"{'QQQ/AI':>10s} {'CAGR':>7s} {'Sharpe':>7s} {'MaxDD':>7s} {'Worst12m':>9s}"
    print("== AI sleeve WITH the 100-day crash switch (the plan's exit) ==")
    print(hdr)
    for ai in [0, 15, 30, 45, 60, 80, 100]:
        c, s, d, w = stats((1 - ai / 100) * qqq + (ai / 100) * ai_gated)
        print(f"{100-ai:>3d}/{ai:<4d} {c*100:6.0f}% {s:7.2f} {d*100:6.0f}% {w*100:8.0f}%")

    print("\n== AI sleeve WITHOUT the crash switch (naked buy-hold basket) — prices the exit ==")
    print(hdr)
    for ai in [30, 60, 100]:
        c, s, d, w = stats((1 - ai / 100) * qqq + (ai / 100) * ew)
        print(f"{100-ai:>3d}/{ai:<4d} {c*100:6.0f}% {s:7.2f} {d*100:6.0f}% {w*100:8.0f}%")

    print("\nCAVEAT: survivorship + one bull regime (~3yr, no in-sample bear). NOT forward returns.")
    print("The tame drawdown on the gated rows is DELIVERED BY THE CRASH SWITCH — see the naked rows.")


if __name__ == "__main__":
    main()
