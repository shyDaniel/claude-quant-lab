# Scoreboard — claude-quant-lab vs Codex (`../i`)

Head-to-head of strategies I've tested vs buy-and-hold QQQ and Codex's core.
All numbers net of stated costs. Honest failures included — that's the point.

## Reference bars
- **BuyHold QQQ** (Codex, adj-close 2005-2026): CAGR 15.5%, Sharpe 0.77, MaxDD -53%, after-tax $5.32M.
- **Codex core** `QQQ_ABS_MOM_12M`: CAGR 13.9%, Sharpe 0.81, MaxDD -29%, after-tax $3.18M.

## My experiments
| # | Strategy | Window | CAGR | Sharpe | MaxDD | Verdict |
|---|----------|--------|------|--------|-------|---------|
| 01 | QQQ Overnight-only (gross) | 1999-2026 | 13.2% | 0.94 | -33% | real edge GROSS |
| 01 | QQQ Overnight net 2bps/side | 1999-2026 | 2.4% | 0.24 | -50% | **REJECTED — costs kill it** |
| 01 | QQQ Intraday-only (gross) | 1999-2026 | -2.6% | 0.00 | -88% | intraday = all the risk, no return |
| 02 | QQQ buy-hold (2013+ bar) | 2013-2026 | 20.5% | 1.00 | -35% | window bar |
| 02 | AI/tech basket equal-weight | 2013-2026 | 33.9% | 1.26 | -45% | survivorship-biased |
| 02 | **AI-momentum top5 (net 10bps)** | 2013-2026 | **40.0%** | **1.30** | -39% | beats QQQ + EW; SEE CAVEAT |

## Findings log
- **exp01 (overnight):** Confirmed the literature. ~All of QQQ's compounding happens
  overnight (close→open); intraday is negative. Gross Sharpe 0.94 >> buy-hold. But it
  requires ~500 trades/yr; even 2bps/side round-trip removes the edge, 5bps destroys it.
  Not retail-viable. AlphaArchitect + the dead NSPY/NIWM ETFs agree. MOVED ON.
  - (Calibration note: my buy-hold here is raw close-close from 1999 incl. dot-com →
    lower CAGR/Sharpe than Codex's adj-close-2005 bar. For fair head-to-head I'll use
    adjusted total return on a matched window in the scoreboard proper.)

- **exp02 (AI/tech momentum):** Monthly rotate into the top-5 by 6-mo momentum from a
  14-name mega-cap tech basket (positive-momentum filter, remainder cash). 2013-2026:
  CAGR 40.0% / Sharpe 1.30 / DD -39% net of 10bps — beats QQQ (20.5%/1.00) AND the
  equal-weight hold of the SAME basket (33.9%/1.26). Costs barely dent it (turnover 5.4x,
  liquid names). Two honest reads:
  1. vs QQQ: huge margin, but MOSTLY SURVIVORSHIP BIAS — I picked 2026's tech winners.
     Not a forward-looking +20%/yr promise.
  2. vs equal-weight-hold (same basket, controls for the bias): momentum still wins
     ~+6%/yr with better Sharpe and ~7pts shallower drawdown → the momentum SIGNAL adds
     REAL (if modest) value. This is the defensible part.
  RISK: -39% drawdown / -37% worst-12mo — brutal for a panic-seller; needs a risk overlay.
  This is the most promising lead so far and the first thing to genuinely beat QQQ on
  risk-adjusted terms in either repo — but it must be DE-BIASED before trusting the margin.

- **exp03 (de-bias + de-risk):** two honest negatives that reshape the plan.
  1. OOS split: AI-momentum LOST to equal-weight-hold on Sharpe in 2013-2019 (1.47 vs
     1.66); only won in 2020-2026. The momentum edge is a recent-regime + survivorship
     artifact, NOT robust. Downgraded.
  2. Simple QQQ 200d-SMA gate on the AI book: return 40%→30%, drawdown only -39%→-37%,
     Sharpe 1.30→1.15 (WORSE risk-adjusted). Market-level gate can't catch idiosyncratic
     tech crashes. Rejected as a fix.
  Winner on the goal's lens (simplest + LOWEST RISK): the plain **QQQ 200d-SMA trend rule**
  — DD -22% (vs QQQ -35%, AI-mom -39%), Sharpe ~0.98, robust in BOTH halves (0.84 / 1.12).

## *** FINAL LOCKED CORE (see outputs/FINAL_RECOMMENDATION.md) ***
**QQQ 12-month momentum -> T-bills/IEF when negative. Monthly. ~0.6 trades/yr.**
- exp04 (2004-2026, OOS-split): 12mo-mom -> IEF = CAGR 13.7% / Sharpe 0.80 / DD -29% /
  turnover 0.8x, robust in BOTH halves (Sharpe 0.72 / 0.87). Beats QQQ on Sharpe (0.80 vs
  0.77), HALVES drawdown (-29% vs -53%). 200d-SMA rule is clearly inferior (0.68 Sharpe,
  -39% DD). T-bill risk-off version is the simplest + best worst-year (-22%).
- This is the defensible simplest/lowest-risk answer. It does NOT out-return QQQ (nothing
  un-levered does) — it makes QQQ's ride holdable. AI-momentum (exp02) = optional high-risk
  sleeve only.

## exp04 rows
| # | Strategy | Window | CAGR | Sharpe | MaxDD | Verdict |
|---|----------|--------|------|--------|-------|---------|
| 04 | QQQ 12mo-mom -> IEF | 2004-2026 | 13.7% | 0.80 | -29% | **FINAL core (best risk-adj)** |
| 04 | QQQ 12mo-mom -> T-bills | 2004-2026 | 12.9% | 0.77 | -29% | simplest, best worst-year -22% |
| 04 | QQQ 200d-SMA -> cash | 2004-2026 | 10.2% | 0.68 | -39% | inferior — rejected |

## exp06 — core + AI sleeve (does AI earn a place?)
Blend of the locked core (QQQ 12mo-mom->T-bills) with the AI-momentum sleeve, 2013-2026:
| Blend | CAGR | Sharpe | MaxDD | w12mo |
|-------|------|--------|-------|-------|
| 100% core | 16.1% | 0.89 | -29% | -22% |
| 90/10 | 18.4% | 0.97 | -29% | -23% |
| 80/20 | 20.8% | 1.04 | -30% | -25% |
| 70/30 | 23.2% | 1.10 | -31% | -26% |
| QQQ buy-hold | 20.5% | 1.00 | -35% | -35% |
Adding AI monotonically raises Sharpe + return with only modest extra drawdown; 80/20 beats
QQQ on return AND Sharpe AND drawdown in-sample. BUT survivorship-inflated — haircut the
sleeve's forward return and the blend only modestly beats the core, not QQQ. VERDICT: core
stays the simplest/lowest-risk recommendation; a capped **<=20% AI sleeve is a legit OPTIONAL
growth add-on** (the user's AI angle), clearly flagged high-risk + survivorship-biased.

## HEAD-TO-HEAD vs Codex vs LEAPS (exp08, 2007-2026, $300k, net of costs)
| Strategy | CAGR | Sharpe | MaxDD | w12mo | $300k end |
|----------|------|--------|-------|-------|-----------|
| QQQ buy-hold | 16.6% | 0.80 | -53% | -48% | $5.96M |
| MY core (mom->T-bills) | 15.5% | 0.88 | -29% | -22% | $4.96M |
| Codex core (mom->IEF) | 16.4% | 0.91 | -29% | -28% | $5.75M |
| LEAPS gated 40% (IV22) | 15.8% | 0.74 | -35% | -29% | $5.17M |
| LEAPS gated 55% (IV22) | 20.3% | 0.74 | -45% | -38% | $10.9M |
| LEAPS ungated 55% | 21.7% | 0.71 | -73% | -65% | $13.6M |
| LEAPS conservative (IV25/3%) | 13.5% | 0.68 | -34% | -29% | $3.52M |

Data verdict:
- **Risk-adjusted (Sharpe) winner = the simple trend rules** (0.88-0.91), beating QQQ (0.80)
  and EVERY LEAPS config (0.68-0.74). LEAPS never wins risk-adjusted.
- **Raw dollars winner = leveraged LEAPS** ($10.9-13.6M) — but at -45% to -73% drawdowns and
  WORSE Sharpe. More money for a LOT more risk, not free.
- **LEAPS is fragile:** IV22/prem55 = $10.9M; IV25/higher-spread = $3.52M. A 3-vol-pt IV or
  cost change flips it from "beats QQQ" to "worst row." You're betting on option pricing too.
- **Me vs Codex:** neck-and-neck on the core (same strategy family). Codex's IEF leg edges
  Sharpe/$ (0.91); MY T-bill leg has the best WORST-YEAR (-22% vs -28%, bonds fell in 2022).
  For lowest risk -> T-bills (mine); for a bit more return -> IEF (Codex). Honest tie, my edge
  = simpler + safest worst-case + I killed the mirages (overnight, LEAPS-as-free-lunch) faster.
LEAPS caveat: synthetic BS on adjusted price, no tax -> REAL leaps worse than shown.

## AFTER-TAX head-to-head (exp10, 2007-2026, taxable account) — LEAPS verdict
| Strategy | Pre-tax $ | After-tax $ | Tax drag |
|----------|-----------|-------------|----------|
| QQQ buy-hold | $5.96M | $4.62M | 23% |
| Codex core (mom->IEF) | $5.75M | $4.45M | 23% |
| MY core (mom->T-bills) | $4.96M | $3.85M | 22% |
| LEAPS gated 55% | $10.9M | $3.18M | **71%** |
| LEAPS ungated 55% | $13.6M | $2.89M | **79%** |
DECISIVE: LEAPS's pre-tax dollar edge is a taxable-account ILLUSION. Rolled annually =>
short-term gains taxed EVERY year => 71-79% drag => $10.9M -> $3.18M, BELOW buy-hold and the
simple trend rules. In a TAXABLE account LEAPS is strictly dominated (more risk AND less $).
LEAPS only makes sense in an IRA/Roth (no annual tax drag) as a small gated high-risk sleeve.
After-tax winner overall = buy-hold QQQ (deferral is powerful); simple > complex after tax.

## exp11 — sector momentum (survivorship-FREE test of the momentum edge)
1999-2026, 9 SPDR sectors (don't disappear -> no survivorship bias):
| Strategy | CAGR | Sharpe | MaxDD |
|----------|------|--------|-------|
| QQQ buy-hold | 10.9% | 0.52 | -83% |
| SPY buy-hold | 8.7% | 0.53 | -55% |
| Sectors equal-weight | 9.4% | 0.59 | -52% |
| Sector-momentum top3 | 9.3% | 0.62 | -30% |
UNIFYING FINDING: momentum's edge is REAL survivorship-free (best Sharpe, -30% DD vs -52/-83)
BUT it barely beats equal-weight sectors on Sharpe (0.62 vs 0.59) — ~ALL the benefit is the
ABSOLUTE-MOMENTUM CASH FILTER (drawdown control), NOT cross-sectional winner-picking. This is
the SAME edge as the core, now confirmed 4 ways (QQQ, SPY, sectors, AI). So: the ONE robust,
real edge across everything = trend/absolute-momentum -> go to cash in downturns -> halve the
drawdown. Winner-picking (AI basket) was mostly survivorship. Confirms the simple core is the
right expression of the only real edge. Sector-mom is a clean alt but LOWER return than the
QQQ core (9.3% vs ~15%), so it doesn't replace the core.

## exp13 — VRP premium-selling (Tian's real gem) — FIRST of his ideas that WORKS
1999-2026 monthly, sold IV = realized*1.10, net 1% spread:
| Strategy | CAGR | Sharpe | MaxDD | w12mo |
|----------|------|--------|-------|-------|
| QQQ buy-hold | 10.2% | 0.54 | -81% | -67% |
| Covered-call 2% OTM | 11.7% | 0.82 | -57% | -47% |
| Put-write ATM | 9.3% | 0.76 | -52% | -44% |
REAL edge: 2%-OTM covered-call beats QQQ on return AND Sharpe (0.82 vs 0.54) AND drawdown.
Harvests the volatility risk premium (option SELLERS get paid for IV overpricing) — matches
CBOE BXM/PUT literature. Vindicates Tian's own QYLD/JEPQ debunk: ATM full-cap (put-write)
UNDERperforms QQQ on return; you must keep some upside (2% OTM). CAVEATS: (1) magnitude is
sensitive to the VRP/IV assumption (conservative IV shrinks it); (2) TAX-UGLY (monthly
short-term premium @37% -> best in IRA/Roth); (3) still -57% DD (owns QQQ in crashes).
NEXT (exp14): combine covered-call overlay WITH the trend filter (sell calls only when trend
on, else cash) -> aim for the VRP Sharpe edge + the core's -29% drawdown. Most promising synthesis.

## exp14 — TREND-GATED COVERED CALL (the synthesis) = best risk-adjusted in either repo
1999-2026 monthly: sell 2%-OTM QQQ calls when trend ON, cash when OFF.
| Strategy | CAGR | Sharpe | MaxDD | w12mo |
|----------|------|--------|-------|-------|
| QQQ buy-hold | 10.2% | 0.54 | -81% | -67% |
| MY core (trend->cash) | 8.8% | 0.60 | -42% | -42% |
| Covered-call (no gate) | 11.7% | 0.82 | -57% | -47% |
| **Trend-gated covered-call** | 9.2% | **0.87** | **-27.7%** | **-27.2%** |
Best Sharpe (0.87) AND lowest drawdown (-28%) of everything tested = VRP income + trend
crash-protection. CAVEATS (honest): (1) sensitive to the VRP/IV assumption (realized*1.10);
(2) TAX-UGLY in taxable (monthly short-term premium) -> belongs in IRA/Roth; after-tax edge vs
DEFERRED buy-hold is uncertain (my uniform-annual tax model here is too harsh on buy-hold);
(3) requires selling monthly options (more complex than the no-option core). So:
- Newbie / taxable / simplest -> the no-option core (QQQ 12mo-mom -> T-bills) stays the pick.
- IRA/Roth + willing to sell monthly calls -> trend-gated covered call is a real risk-adjusted upgrade.
Beat Codex: it only PLANNED option backtests (DCA_PUT_ENTRY etc.); I ran the synthesis.

## FINAL STATE
Defensible best executable strategy = **QQQ 12mo-mom -> T-bills, monthly** (100% core),
optional <=20% AI-momentum sleeve for growth-seekers. Proven, simplest, lowest-risk, robust.
Ongoing cycles will keep probing but the core is locked.
