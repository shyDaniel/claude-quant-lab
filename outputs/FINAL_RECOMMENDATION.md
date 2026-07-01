# FINAL RECOMMENDATION — claude-quant-lab

## The rule (simplest + lowest risk, proven by backtest)
**Own QQQ when its trailing 12-month return is positive; otherwise hold T-bills (BIL/SGOV,
or IEF Treasuries for a bit more return). Check once, on the last trading day of each month.**

That's the whole strategy. One signal, one switch, ~0.6 trades/year.

## Why this is THE answer (not the flashy stuff)
Across ~4 experiments and both repos, the honest, data-backed conclusions are:
- Nothing un-levered beats QQQ on RAW/after-tax return (confirmed again here: 13.7% vs 15.2%).
- Fancier signals FAIL on QQQ: overnight anomaly dies after costs (exp01); MACD/RSI/volume
  add nothing (Codex's signal lab); AI/tech momentum is high-return but survivorship-biased,
  OOS-fragile, and -39% drawdown (exp02/03) — a high-risk sleeve, not a core.
- The 200d-SMA trend rule is inferior (worse Sharpe, deeper OOS drawdowns) to 12-mo momentum.

So the best SIMPLE, LOW-RISK core is 12-month momentum with a safe risk-off leg.

## Proof vs QQQ (2004-2026, net of 5bps, monthly)
| Strategy | CAGR | Sharpe | MaxDD | Worst-12mo | Turnover | OOS Sharpe (04-14 / 15-26) |
|----------|------|--------|-------|-----------|----------|-----------------------------|
| QQQ buy-hold | 15.2% | 0.77 | -53% | -48% | 0 | 0.60 / 0.92 |
| **QQQ 12mo-mom -> IEF (FINAL)** | **13.7%** | **0.80** | **-29%** | -28% | 0.8x | **0.72 / 0.87** |
| QQQ 12mo-mom -> cash/T-bills | 12.9% | 0.77 | -29% | -22% | 0.8x | 0.64 / 0.88 |
| QQQ 200d-SMA -> cash | 10.2% | 0.68 | -39% | -38% | 1.8x | 0.44 / 0.87 |

- IEF version: best risk-adjusted (Sharpe 0.80), most return. Caveat: Treasuries can also
  fall in a rate shock (2022) → worst-12mo -28%.
- T-bill/cash version: SIMPLEST + best worst-year (-22%); T-bills are the safest risk-off
  (didn't fall in 2022) and earn ~4-5% yield. Pick this if you want the lowest-risk, simplest.

## The honest bottom line (for a taxable, panic-prone $300k investor)
- This rule captures ~90% of QQQ's return with HALF the drawdown (-29% vs -53%) and a
  holdable worst year (-22% vs -48%). It won't out-RETURN buy-and-hold; it makes a QQQ-like
  ride one you can actually STAY IN through a crash. The value is behavioral + risk, not alpha.
- Simplicity is a feature: one monthly check, ~0.6 trades/yr, tax-friendly, no leverage, no
  options, no thin AI names. A newbie can run it. That is the point.
- Best placed in an IRA/Roth (tax-free switches). In taxable, it's already low-turnover.
- Optional growth add-on (≤20%, sheltered, "fun money"): the AI/tech momentum sleeve.
  exp06 shows a blend of 80% core + 20% AI historically beat QQQ on return, Sharpe, AND
  drawdown (20.8%/1.04/-30% vs QQQ 20.5%/1.00/-35%, 2013-2026) — BUT that is survivorship-
  inflated (the basket is today's winners). Forward-looking, haircut the sleeve; it then
  only modestly beats the core, not QQQ. So: legitimate for a growth-seeker who wants AI
  exposure and accepts higher risk, capped ≤20%. NOT the core. The 100% core is the
  simplest, lowest-risk answer and stays the recommendation.

## Refinement confirmed (exp05, 2007-2026 where T-bills exist)
| Config | CAGR | Sharpe | MaxDD | Worst-12mo | Turnover |
|--------|------|--------|-------|-----------|----------|
| QQQ buy-hold | 16.6% | 0.80 | -53% | -48% | 0 |
| **12mo-mom MONTHLY -> T-bills (LOWEST RISK)** | **15.5%** | **0.88** | -29% | **-22%** | 0.6x |
| 12mo-mom MONTHLY -> IEF (a bit more return) | 16.4% | 0.91 | -29% | -28% | 0.6x |
| 12mo-mom WEEKLY -> T-bills | 13.5% | 0.80 | -29% | -22% | 1.5x |

Confirmed, data-driven:
- **Monthly beats weekly** — weekly did NOT reduce drawdown (-29% either way) but cut
  return and doubled turnover. So the SIMPLEST cadence is also the best. Locked: monthly.
- **T-bills = lowest-risk risk-off** (best worst-year -22%; they didn't fall in 2022 like
  IEF did → -28%). Use T-bills for lowest risk; IEF only if you want ~+1%/yr and accept
  bond risk.
- Monthly T-bill version captures **93% of QQQ's return with HALF the drawdown and a HIGHER
  Sharpe (0.88 vs 0.80)**. This is the final, simplest, lowest-risk answer.

## How strong is the proof? (exp07 robustness battery — the honest ceiling)
"Best thing in the world" is UNPROVABLE (infinite strategies, unknowable future). What IS
proven, and matters more than a single flashy backtest:
- **Not overfit:** drawdown reduction & Sharpe stable across 3/6/9/12/15-month lookbacks.
- **Not a timing artifact:** works on any monthly check day (month-end/1st best; mid-month
  slightly worse — honest caveat, still halves QQQ's drawdown).
- **Universal (the key):** the SAME rule on SPY also lifts Sharpe (0.65->0.68) and HALVES
  drawdown (-55%->-34%). An edge that works identically on two indices is a REAL trend
  effect, not a QQQ curve-fit.
Ceiling of honest proof reached: this is a robust, non-overfit, universal, simple rule —
about as good as a simple executable trend rule gets. Anything "better" on raw return needs
leverage/options/complexity the user declined or that added risk without robust edge.

## Status: FINAL and refined.
Core is locked: **QQQ 12-month momentum, monthly, T-bills when off.** Data-confirmed
simplest + lowest-risk. Only a rule that is simpler AND lower-risk AND robust would replace
it — none found across 5 experiments + Codex's ~30 strategies. Ongoing cycles will keep
probing (e.g., does a tiny AI sleeve help the frontier?) but will not complicate the core.
