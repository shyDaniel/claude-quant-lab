"""AI-capex thesis assistant — signal, not noise. Run daily (cron). Only flags ACTION.

Emits: (1) trades to make TODAY (names that crossed their 100d trend), (2) watchlist
(about to flip), (3) regime (risk-on/off), (4) status per name. This is the mechanical
brain; an LLM layer can later summarize *why* from news — but the actionable core is here.
"""
from __future__ import annotations
import yfinance as yf, numpy as np, pandas as pd
BASKET=["NVDA","AMD","AVGO","MU","SNDK","MRVL","STX","ANET","VST","CEG","GEV","VRT"]
N=100

def run():
    px=yf.download(BASKET+["QQQ"],period="1y",auto_adjust=True,progress=False)["Close"].dropna(how="all")
    ma=px[BASKET].rolling(N).mean()
    above=px[BASKET]>ma
    last=px[BASKET].iloc[-1]; ma_last=ma.iloc[-1]
    # crosses in last 5 sessions
    crossed_up=[t for t in BASKET if (~above[t].iloc[-6:-1]).any() and above[t].iloc[-1] and not above[t].iloc[-6]]
    crossed_dn=[t for t in BASKET if (above[t].iloc[-6:-1]).any() and not above[t].iloc[-1] and above[t].iloc[-6]]
    dist={t:(last[t]/ma_last[t]-1)*100 for t in BASKET}
    watch=[t for t in BASKET if abs(dist[t])<=3]                      # near flip
    on=[t for t in BASKET if last[t]>ma_last[t]]
    # basket-level regime (equal-weight NAV vs its own 100d MA)
    nav=(1+px[BASKET].pct_change().mean(axis=1).fillna(0)).cumprod()
    regime="RISK-ON" if nav.iloc[-1]>nav.rolling(N).mean().iloc[-1] else "RISK-OFF (basket below trend -> raise cash)"
    d=px.index[-1].date()
    print(f"===== AI-CAPEX ASSISTANT — {d} =====")
    print(f"REGIME: {regime}   |   {len(on)}/12 names ON   |   target each ON name = {100/max(len(on),1):.0f}% of sleeve\n")
    print("[1] ACT TODAY:")
    if crossed_up: print(f"   BUY  (reclaimed 100d): {', '.join(crossed_up)}")
    if crossed_dn: print(f"   SELL (broke 100d):     {', '.join(crossed_dn)}")
    if not crossed_up and not crossed_dn: print("   nothing crossed in last 5 sessions — HOLD current positions.")
    print(f"\n[2] WATCH (within 3% of flipping): {', '.join(f'{t}({dist[t]:+.0f}%)' for t in watch) or 'none'}")
    print("\n[3] STATUS:")
    for t in sorted(BASKET,key=lambda x:-dist[x]):
        print(f"   {t:5s} {'ON ' if t in on else 'OUT'}  {dist[t]:+5.0f}% vs 100d")

if __name__=="__main__": run()
