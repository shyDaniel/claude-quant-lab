# Less-QQQ / more-AI + buy-the-dip — answers (2026-07-01)

User asked (wants MORE risk, no emergency money in play): (1) backtest less QQQ / more AI,
(2) backtest "buy the dip" (what they're doing today), (3) what other AI stock to buy.

> **Data note:** live prices (Yahoo/Stooq/Nasdaq/AlphaVantage/Tiingo) are ALL blocked by the
> cloud sandbox egress policy, so fresh backtests can't run here. `exp22_ai_tilt_sweep.py` and
> `exp23_buy_the_dip.py` are written to run LOCALLY. The answers below come from backtests this
> repo ALREADY ran and recorded (exp06, exp19, exp21) — real numbers, same caveats.

## 1. Less QQQ, more AI — what the backtests show
**exp06** (2013-2026, QQQ-core + AI-momentum sleeve, survivorship-inflated):

| QQQ / AI | CAGR | Sharpe | MaxDD | Worst-12mo |
|----------|------|--------|-------|-----------|
| 100 / 0  | 16.1% | 0.89 | -29% | -22% |
| 90 / 10  | 18.4% | 0.97 | -29% | -23% |
| 80 / 20  | 20.8% | 1.04 | -30% | -25% |
| 70 / 30  | 23.2% | 1.10 | -31% | -26% |
| QQQ buy-hold (ref) | 20.5% | 1.00 | -35% | -35% |

**exp19** (~3yr, going nearly ALL-in on the AI-capex supply-chain basket):

| Strategy | CAGR | Sharpe | MaxDD |
|----------|------|--------|-------|
| QQQ buy-hold | 27% | 1.27 | -23% |
| AI-capex basket, naked hold | 129% | 2.25 | **-43%** |
| AI-capex basket + 100d crash switch | 99% | 2.18 | -22% |

**Read:** in-sample, adding AI raised BOTH return and Sharpe, and the 100-day crash switch held
drawdown near QQQ's. So "more AI" looks like a free lunch *in the backtest*. It is not:
- These are **2026's winners** measured over **one AI-capex boom** with **no in-sample bear**.
  Forward returns will be **dramatically lower**; memory/semis crash **-50% to -70%** historically.
- The tame -22% drawdown is **manufactured entirely by the crash switch**. Naked, the basket was
  **-43%**, and that's without a real cyclical bust in the sample. No switch → no case for sizing up.

**Verdict for you:** your locked plan already runs an aggressive **30% AI** tier. The recommendation
doc's honest lines still hold: **30% = defensible-aggressive** (given the exit); **40-45% = conviction
over evidence** — survivable at your income, past what a skeptical auditor signs off on; **>50% = betting
the farm on one regime.** You want more risk — 40% AI is the honest ceiling I'd put my name near, and
ONLY with the crash switch armed. Note you are ALREADY ~37% of the account in single AI names.

## 2. Buy the dip — the backtest says it HURT (this is the important one)
**exp21** tested "own what's weak (dip)" vs "own what's strong" on the AI basket. Recorded verdict:
> *buy-the-dip (buying weakness) QUARTERS returns; buy-strength + crash switch is the best of tested.*

For momentum-driven single names (NVDA/MU/semis), buying the dip = **catching a falling knife**: in a
cyclical downturn these keep falling, and the dip-buyer keeps averaging into the loser. Buying *strength*
(names above their 100d) with a crash exit did far better. `exp23` re-runs this on QQQ and the basket.

Nuance that matters: "buy the dip" behaves **very differently** on a diversified index vs a single stock.
- **QQQ** always recovered historically, so deploying cash you were going to invest *anyway* on dips is
  roughly fine — but **lump-sum still beats waiting for dips ~2/3 of the time** (markets rise; waiting =
  cash drag). exp23 part (A) quantifies this.
- **Single semis in a cyclical crash** have no guarantee of recovery on your timeline. Dip-buying MU/NBIS
  into a memory bust is the classic way to get run over. That's the -50/-70% risk, live.

**So:** what you're doing today (buying the dip in AI names, with SOXL -14.7% / CRWV -12.3% on the tape)
is exactly the behavior the backtest ranks WORST for these names — UNLESS you pair it with the trend/crash
exit. Buy strength + exit on the 100d break, not weakness.

## 3. What other AI stock to buy
You're heavily concentrated in **MEMORY** (MU, DRAM, + NBIS/SMCI adjacent). The single most useful move
isn't "one more AI name" — it's **diversifying ACROSS the AI supply chain** so one memory-cycle crash
doesn't take the whole sleeve. From the exp19 basket, the pieces you're missing:

| Layer | Tickers you don't hold | Why it diversifies you |
|-------|------------------------|------------------------|
| Compute / custom silicon | **AVGO**, AMD, MRVL | AVGO = highest-quality large-cap AI compute+networking; less memory-cyclical than MU |
| AI networking | ANET, MRVL | data-center interconnect; different demand driver than memory |
| **Power & cooling** | **VRT**, VST, CEG, GEV | the *next* bottleneck (data-center power/cooling); **lowest correlation to the memory cycle** |
| Storage | SNDK, STX | same supercycle as your memory names — adds concentration, not diversification |

If I had to name two: **AVGO** (quality compute/networking, less fragile than another memory bet) and
**VRT** (data-center power/cooling — a genuinely different driver from what you already own). This spreads
the *same thesis* across more of the chain instead of tripling down on memory.

**Honesty line:** this is the AI-capex *thesis* basket — survivorship-flavored, not a proven edge. I'm not
predicting these go up; I'm saying if you're expressing the AI-capex view aggressively, own the whole
supply chain (compute + networking + power), not a memory-heavy corner of it — and keep the crash switch
on every name. You're paid for taking the risk, not for a proven edge.
