# Study: Tian Compounding (天哥复利之道) — ideas + honest tests

Chinese-language YouTube channel, 66 videos, "million-dollar challenge" real-money series.
Subtitles are DISABLED on his videos (can't pull transcripts — yt-dlp & transcript API both
blocked; Codex will hit the same wall). Studied via titles + video descriptions + web research.

## His core ideas (extracted from descriptions)
1. **Leveraged core-satellite QQQ + SMA200 trend filter** (his headline):
   60% QQQ + 30% QLD(2x) + 10% TQQQ(3x), gated by SMA200 + hysteresis. Claims 27x / ~2x QQQ
   return, recent-5yr DD -33%.
2. **Deep-ITM LEAPS + RSI(14) dip-buy + PMCC** (Poor Man's Covered Call to cut cost basis).
   Claims 99% win rate, 14yr 13.8x.
3. **Premium SELLING for income**: Sell Put (cash-secured), Covered Call, the Wheel, PMCC,
   calendar spreads, iron condors. "Golden delta" (~0.16-0.30), manage/close ~21 DTE, high
   win rates (harvesting the volatility risk premium). This mirrors tastytrade research.
4. **70/25/5 or 60/30/10 allocation** with laddered profit-taking + FIFO rotation.
5. LEAPS "infinite roll" to a negative cost basis.

## My honest tests / verdicts
- **[TESTED, exp12] Leveraged trend-filter (60/30/10 + SMA200):** does NOT beat QQQ over full
  1999-2026 with realistic expense(0.95%)+financing(3%). Result: 9.7% CAGR (< QQQ 10.3%),
  Sharpe 0.49 (=QQQ), MaxDD -72%. His 27x/-33% is a RECENT-BULL + LOW-RATE artifact — leveraged
  ETFs are simulated pre-2010 and his window skips the dot-com/GFC leverage massacre where the
  filter whipsaws a 1.5x book. Verdict: REJECTED as a full-cycle strategy (same leverage trap
  we already found). It DOES win in sustained bull/low-rate regimes — but that's regime-timing.
- **[PRIOR] LEAPS buying** (his #2): I already showed it's a taxable-account illusion (exp08/10)
  — after-tax dominated. His PMCC (selling calls vs LEAPS) changes economics via premium income.

## GENUINELY USEFUL ideas worth testing (the VRP is the real one)
- **Premium selling / VRP harvest (Wheel, cash-secured puts, covered calls on QQQ):** this is a
  REAL, documented edge (the volatility risk premium — option SELLERS get paid for the same IV
  overpricing that makes BUYING LEAPS bad). High win rate, negative skew (rare big losses in
  crashes). NEXT TEST: does a systematic sell-put / covered-call overlay on QQQ improve
  risk-adjusted return after costs + tax vs my core? This is the one Tian idea that could add.
- **Hysteresis buffer on the trend filter** — a cheap, sensible refinement to reduce whipsaw
  (worth folding into the core rule).
- **RSI(14) dip-buy as an ENTRY timing overlay** — minor; test if it improves the core's entries.

## Bottom line
Tian's leveraged/LEAPS headline numbers are backtest-optimistic (recent-regime, low-rate,
pre-tax, simulated leverage). His durable contribution to MY strategy is the PREMIUM-SELLING
(VRP) angle — the one thing I haven't tested and the opposite of the LEAPS-buying I debunked.
