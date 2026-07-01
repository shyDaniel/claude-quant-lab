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

## LEADING FINAL CANDIDATE (simplest + lowest risk, refine from here)
A simple QQQ trend rule is the low-risk core. Both repos independently converge here.
My job: find the SIMPLEST, LOWEST-RISK variant with the best robust risk-adjusted return,
and lock it. AI-momentum stays a documented high-risk/high-return sleeve, NOT the core.

## Next
- exp04: pick the FINAL low-risk core — compare QQQ 200d-SMA vs 12-mo momentum vs a
  dual-momentum (QQQ-on / defensive-asset-off), all OOS + after-tax, choose the simplest
  with the best robust Sharpe & shallowest drawdown. Lock it as the recommendation.
