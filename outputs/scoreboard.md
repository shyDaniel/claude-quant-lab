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

## Next
- exp03: DE-BIAS the momentum result — (a) broader/less-cherry-picked universe, (b) OOS
  split (does momentum beat EW in BOTH halves?), (c) add a trend/QQQ risk-off overlay to
  cut the -39% drawdown. This decides if exp02 is a real edge or a survivorship mirage.
- exp04: trend-gated deep-ITM LEAPS, my own honest costs (independent of Codex's ~19.7%).
