# Due Diligence — claude-quant-lab AI/QQQ Strategy Research
**Prepared for independent AI audit. Author: Claude (Anthropic). Date: 2026-07-01.**
**Status: research output, NOT financial advice. Designed to be adversarially reviewed — every material limitation is disclosed below; if you (the auditor) find one not listed here, that is a finding against this document.**

---

## 0. TL;DR for the auditor
- The headline "AI-capex basket returns 100–130%/yr" numbers are **REAL as backtests but NOT forward-looking**: they are inflated by (a) **survivorship bias** (the basket = 2026's known winners), (b) a **single, extraordinary regime** (the 2023–2026 AI-capex + memory supercycle), and (c) **short history** (2–3 years, no in-sample bear market for these names). Treat them as an illustration of a *thesis*, not an expected return.
- The **robust, defensible** conclusions (which survived bootstrap / OOS / after-tax): (1) nothing un-leveraged reliably beats buy-and-hold QQQ *after tax over full cycles*; (2) a simple 12-month-momentum trend rule reliably **halves drawdown** (statistically significant) but does **not** significantly beat QQQ on Sharpe; (3) a trend-gated covered call is the only strategy with a statistically-significant risk-adjusted edge over QQQ, and it is **IRA/Roth-only** (tax-dominated in a taxable account).
- **Primary risks to the recommended AI-capex tilt:** cyclical reversal (memory/semis crash -50–70% historically), overfitting from testing many variants on one dataset, and single-source data.

---

## 1. Scope & objective
Independent research to find a strategy that beats buy-and-hold QQQ on a risk-adjusted basis, for a specific investor (age 26, ~$278.6k taxable brokerage cash, ~$50k savings, ~$160k 401k, ~$260k pre-tax income, high risk capacity, works at OpenAI, wants concentrated AI exposure). ~21 numbered experiments (exp01–exp21) plus decompositions. Full code in this repo.

## 2. DATA SOURCES (auditor: scrutinize this section hardest)
- **Sole price source: Yahoo Finance**, accessed via the `yfinance` Python package (v as installed 2026-06). Unofficial, free, research-only. **No second source was successfully used for cross-validation** (an attempted Stooq reconciliation failed; this is a known unmitigated single-source risk).
- **Adjustment:** `auto_adjust=True` (dividends + splits reinvested → total-return proxy) for most tests. The overnight/intraday decomposition (exp01) intentionally used **raw** Open/Close (not dividend-adjusted; ~0.6%/yr QQQ dividend omitted there — immaterial to that conclusion).
- **Known data-quality events:**
  - MU (Micron) showed ~$1,154 / ~$1.3T market cap. I initially flagged this as a likely data error (my knowledge cutoff is Jan 2026). It was CONFIRMED REAL (AI memory/HBM supercycle) via yfinance `marketCap`. Lesson: my priors were stale; auditor should independently confirm current prices.
  - SNDK reported +4,957% 1-yr — extreme; consistent with the storage supercycle but auditor should verify.
- **yfinance/yt-dlp caveats:** possible survivorship in delisted names (not adjusted for), occasional bad ticks, no point-in-time index constituents (see §6).

## 3. TIME SPANS (per experiment — they vary and this matters)
| Asset group | Window used | Why / limitation |
|---|---|---|
| QQQ (core rules) | 1999–2026, and matched 2004/2005/2007–2026 | Full history incl. dot-com + GFC where possible. Different windows are NOT directly comparable — noted inline. |
| QQQ options/LEAPS/covered-call sims | 1999–2026 monthly | Synthetic (Black-Scholes), see §5. |
| AI-capex basket (NVDA/AMD/AVGO/MU/SNDK/MRVL/STX/ANET/VST/CEG/GEV/VRT/NBIS) | **~2–3 years only (2023–2026)** | **CRITICAL LIMITATION.** Several names are recent listings: CEG (2022), NBIS (relisted 2024), GEV (2024), SNDK (2025), VRT (2018), VST (2016). No pre-2023 history; **no in-sample bear market** for this basket. |
| Sector SPDRs (survivorship-free test) | 1999–2026 | The one clean, long-history momentum test. |
| Single-stock 2x ETF sims | 2023–2026, simulated | Daily-reset simulated from underlying; see §5. |

## 4. METHODOLOGY
- **Backtests:** vectorized pandas; daily returns; positions applied **next period (signals `.shift(1)`)** to avoid look-ahead. Rebalance monthly (month-end) or weekly, as stated per test.
- **Costs modeled:** stocks 5–10 bps per trade (turnover-weighted); options 1–3% of premium (spread); leveraged ETFs 0.95% expense + ~5% financing on borrowed notional. **These are assumptions; real slippage on concentrated/thin names may be higher.**
- **After-tax:** LTCG 23.8% (incl. NIIT), short-term 40.8%, Section-1256 blended 30.6%. Models: "deferred" (tax once at liquidation, buy-hold/low-turnover) vs "annual realization" (options/high-turnover). **Approximate: no state tax, no lot-level tracking, no wash sales.**
- **Statistical significance:** stationary/block bootstrap, 5,000 resamples, block ≈ 6 months, reporting P(strategy beats benchmark) and 90% CIs.
- **Metrics:** CAGR, annualized Sharpe (rf≈0 unless noted — inflates Sharpe modestly), max drawdown, worst rolling 12-month, turnover.

## 5. SYNTHETIC INSTRUMENTS (not real fills — read before trusting any options/leverage number)
Options (LEAPS, covered calls), and leveraged ETFs were **simulated**, not backtested on real quotes:
- Options priced via **Black-Scholes** with IV = trailing realized vol × 1.10 (and sensitivity to flat 20–25% IV). Real IV, bid/ask (often 1–3%+/side), early exercise, and dividends make real results **worse** than shown. These numbers are **optimistic ceilings**.
- 2x/3x ETFs simulated as `L × daily return − (expense+financing)`; captures daily-reset decay/compounding but not tracking error or gaps. Single-stock leveraged ETFs are high-risk products (SEC-warned).

## 6. KEY LIMITATIONS & BIASES (the heart of the audit)
1. **Survivorship bias (SEVERE for AI baskets).** The AI-capex names are today's winners chosen in 2026 and backtested over the period they won. This alone likely explains most of the AI basket's excess return. A point-in-time / delisting-adjusted universe was NOT available. Forward returns will be dramatically lower.
2. **Regime / recency dependence.** 2023–2026 = a historic AI-capex boom + memory supercycle. 100–130% CAGRs are regime artifacts. Memory/semis are the most cyclical sector in tech (historical -50–70% crashes). No in-sample downturn for these names.
3. **Overfitting / multiple testing.** ~21 experiments + many variants (MA lengths 50/100/150, RSI thresholds, per-name vs basket gates, IV multipliers, etc.) were run on the same data and the winners reported. The exact "best" parameters are within noise. The "buy-strength + crash-switch" upgrade (exp21) is the newest and least-validated (highest overfitting risk).
4. **Single data source, no cross-validation** (§2).
5. **Synthetic options/leverage** (§5) — optimistic.
6. **After-tax approximations** (§4) — no state tax, no lot tracking.
7. **Short backtest for the AI thesis** (2–3 yrs) — tiny sample.
8. **Author knowledge cutoff (Jan 2026)** — missed the storage supercycle initially; blind to post-cutoff fundamentals.
9. **rf≈0 Sharpe** slightly inflates all Sharpes.
10. **Behavioral assumption:** the entire "trend rule beats buy-hold for this user" thesis rests on the user actually following the exit and not panic-selling — unverifiable.

## 7. FINDINGS (full catalog; numbers are backtests under the caveats above)
| Exp | Test | Window | Result | Verdict |
|---|---|---|---|---|
| 01 | QQQ overnight vs intraday | 1999–2026 | Overnight gross Sharpe 0.94; dies at ~2bps/side | REJECTED (cost trap) |
| 02/03 | Mega-cap AI momentum | 2013–2026 | 40% CAGR but OOS-fragile, survivorship | Sleeve only |
| 04/05 | Simple QQQ trend cores | 2004–2026 | 12mo-mom→T-bills: 13–15% CAGR, DD −29% vs QQQ −53% | CORE (simple) |
| 06 | Core + AI blend | 2013–2026 | 80/20 beats QQQ in-sample; survivorship-inflated | Optional |
| 07 | Robustness (lookback/day/cross-asset) | 2004–2026 | Trend edge works on SPY too; drawdown-reduction stable | Not overfit (this one) |
| 08/10/15/17 | LEAPS + covered calls + tax | 1999–2026 synth | Options tax-dominated in taxable; covered call IRA-only | See §0 |
| 09/16 | Bootstrap significance | 1999–2026 | Core Sharpe edge NOT significant; covered-call edge IS (97.7%) | Honest correction |
| 11 | Sector momentum (survivorship-free) | 1999–2026 | Momentum edge real but modest; benefit = the cash filter | Unifying |
| 12 | Leveraged QQQ (Tian) | 1999–2026 | 60/30/10+SMA200 does NOT beat QQQ full-cycle, −72% DD | REJECTED |
| 13/14 | VRP covered call, trend-gated | 1999–2026 synth | Sharpe 0.87 IRA-only | Best risk-adj (sheltered) |
| 18 | AI sleeve after-tax | 2013–2026 | Even biased blend loses to QQQ after tax in taxable | Sheltered only |
| 19 | QQQ decomposition + AI-capex basket | 3mo / 3yr | MU+AMD = ~18% of QQQ's 3mo move; basket 129% CAGR | Thesis (regime) |
| 20 | Trend-managed AI-capex + assistant | 3yr | 100–110% CAGR, DD −19 to −22% | Recommended structure |
| 21 | Buy-strength vs buy-dip; +crash switch | 3yr | Buy-dip QUARTERS returns (29% vs 113%); buy-strength+crash-switch 130%/−26% | Upgrade (least validated) |

## 8. RECOMMENDED STRATEGIES (and their honest status)
1. **Simple core (robust):** QQQ 12-month momentum → T-bills; monthly. Halves drawdown vs QQQ; drawdown edge is bootstrap-significant, Sharpe edge is NOT. Does not out-return QQQ.
2. **AI-capex tilt (thesis, high-risk, regime-dependent):** concentrate in the AI supply chain (memory/storage/compute/power/cooling), own names above their 100-day (or strongest momentum), exit to cash on a sector-level 100-day break. Backtest 100–130% CAGR over 2023–2026 **is survivorship+regime inflated — not an expected return.** Value = the crash-exit discipline.
3. **Trend-gated covered call (IRA/Roth only):** statistically-significant Sharpe edge; tax-dominated in taxable.
Proposed allocation given the user's risk appetite: ~40% QQQ / ~45% AI-capex tilt / ~15% sandbox. This is aggressive; a conservative reviewer would argue for far less than 45% in a survivorship-biased, single-regime basket.

## 9. CLAIMS AN AUDITOR SHOULD INDEPENDENTLY VERIFY
- Current prices/market caps (MU ~$1.3T, SNDK, etc.) against a second source (Bloomberg/broker).
- Re-run every backtest with a **point-in-time, delisting-adjusted universe** — the AI-basket edge will shrink substantially.
- Re-run the AI basket including a **simulated -50 to -70% memory/semi downturn** to stress the drawdown claims (there is none in-sample).
- Apply **realistic option spreads and real IV** to the covered-call/LEAPS numbers.
- Apply a **deflated Sharpe / multiple-testing correction** across all ~21 experiments (not done here).
- Check the after-tax models against a real tax engine incl. state tax.

## 10. REPRODUCIBILITY
- Repo: `/Users/hanyusong/Documents/Codex/2026-06-30/claude-quant-lab` (git; ~22 commits).
- Code: `src/qlab/exp01_*.py … exp21`, `ai_assistant.py`. Results log: `outputs/scoreboard.md`. Recommendation: `outputs/FINAL_RECOMMENDATION.md`.
- Environment: Python 3.12, pandas/numpy/yfinance. Data re-pulls live from Yahoo on each run (so numbers will drift as prices move).
- A parallel project ("Codex", `../i`) independently reached the SAME core conclusion (buy-hold QQQ + 12-mo momentum), which is corroborating — but note both used the same yfinance source and may share its biases.

## 11. BOTTOM LINE (honest)
The **durable** finding is unglamorous: buy-and-hold QQQ is very hard to beat after tax; a simple trend rule buys drawdown insurance, not alpha. The **exciting** finding (AI-capex concentration) is real *as a thesis about where AI spending is flowing right now*, but its backtested returns are **not trustworthy as forward estimates** due to survivorship, regime, and short history. Anyone acting on the AI tilt is making a **discretionary, high-conviction, high-risk bet on the AI-capex cycle continuing**, mitigated only by a trend-exit and position sizing — not a statistically proven edge.
