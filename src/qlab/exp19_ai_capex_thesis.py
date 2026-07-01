"""Exp19 — QQQ decomposition + AI-capex supply-chain basket + basket-level trend gate.
Committed post-audit (was run inline). CAVEATS: survivorship (2026 winners), ~3yr single
regime, single-source yfinance. Numbers are NOT forward estimates. See outputs/DUE_DILIGENCE.md.
"""
from __future__ import annotations
import yfinance as yf, numpy as np, pandas as pd
BASKET=["NVDA","AMD","AVGO","MU","SNDK","MRVL","STX","ANET","VST","CEG","GEV","VRT","NBIS"]
def stats(r):
    r=r.dropna(); eq=(1+r).cumprod()
    return (eq.iloc[-1]**(252/len(r))-1, r.mean()/r.std()*np.sqrt(252), (eq/eq.cummax()-1).min())
def main():
    px=yf.download(BASKET+["QQQ"],period="3y",auto_adjust=True,progress=False)["Close"].dropna(how="all")
    ew=px[BASKET].pct_change().mean(axis=1)
    nav=(1+ew.fillna(0)).cumprod()
    gate=(nav>nav.rolling(100).mean()).shift(1).fillna(False)   # basket-level 100d trend gate
    for name,r in {"QQQ":px["QQQ"].pct_change(),"AI-capex basket (hold)":ew,
                   "AI-capex + basket 100d gate":pd.Series(np.where(gate,ew,0.0),index=px.index)}.items():
        c,s,d=stats(r); print(f"{name:32s} CAGR {c*100:5.0f}%  Sharpe {s:.2f}  MaxDD {d*100:.0f}%")
    print("CAVEAT: survivorship + single regime; not a forward estimate.")
if __name__=="__main__": main()
