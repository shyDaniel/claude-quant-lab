"""Exp21 — buy-strength vs buy-the-dip, and adding a sector crash switch. Committed post-audit.
CAVEATS as exp19. High turnover (short-term tax). Multiple-testing/overfitting risk across variants.
"""
from __future__ import annotations
import yfinance as yf, numpy as np, pandas as pd
B=["NVDA","AMD","AVGO","MU","SNDK","MRVL","STX","ANET","VST","CEG","GEV","VRT","NBIS"]
def stats(r):
    r=r.dropna(); eq=(1+r).cumprod(); return (eq.iloc[-1]**(252/len(r))-1, r.mean()/r.std()*np.sqrt(252),(eq/eq.cummax()-1).min())
def main():
    px=yf.download(B,period="3y",auto_adjust=True,progress=False)["Close"].dropna(how="all")
    me=px.index.to_series().groupby(px.index.to_period("M")).transform("max")==px.index
    navb=(1+px.pct_change().mean(axis=1).fillna(0)).cumprod()
    crash_ok=(navb>navb.rolling(100).mean()).shift(1).fillna(False)
    d=px.diff(); up=d.clip(lower=0).rolling(14).mean(); dn=(-d.clip(upper=0)).rolling(14).mean(); rsi=100-100/(1+up/dn)
    ma100=px.rolling(100).mean()
    def run(pick,crash=False):
        sig=pick.shift(1); w=pd.DataFrame(np.nan,index=px.index,columns=B)
        for t in px.index[me]:
            on=sig.loc[t].fillna(False)
            if crash and not bool(crash_ok.loc[t]): on=on&False
            n=int(on.sum()); w.loc[t]=on.astype(float)/n if n else 0.0
        return (w.ffill().fillna(0.0).shift(1)*px.pct_change()).sum(axis=1)
    for name,r in [("buy-hold",px.pct_change().mean(axis=1)),("buy the rip (RSI>60)",run(rsi>60)),
                   ("buy the rip + crash switch",run(rsi>60,True)),("buy the dip (below 100d)",run(px<ma100)),
                   ("above-100d + crash switch",run(px>ma100,True))]:
        c,s,dd=stats(r); print(f"{name:30s} CAGR {c*100:5.0f}%  Sharpe {s:.2f}  MaxDD {dd*100:.0f}%")
    print("VERDICT: buy-the-dip (weakness) quarters returns; buy-strength + crash switch is best of tested,")
    print("but this is the LEAST-validated result (most variants tried) — high overfitting risk.")
if __name__=="__main__": main()
