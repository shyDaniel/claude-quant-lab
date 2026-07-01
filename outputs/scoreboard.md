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

## Findings log
- **exp01 (overnight):** Confirmed the literature. ~All of QQQ's compounding happens
  overnight (close→open); intraday is negative. Gross Sharpe 0.94 >> buy-hold. But it
  requires ~500 trades/yr; even 2bps/side round-trip removes the edge, 5bps destroys it.
  Not retail-viable. AlphaArchitect + the dead NSPY/NIWM ETFs agree. MOVED ON.
  - (Calibration note: my buy-hold here is raw close-close from 1999 incl. dot-com →
    lower CAGR/Sharpe than Codex's adj-close-2005 bar. For fair head-to-head I'll use
    adjusted total return on a matched window in the scoreboard proper.)

## Next
- exp02: cross-sectional momentum on a curated AI/tech basket vs QQQ (the user's angle,
  Codex botched it). HIGH priority.
- exp03: trend-gated deep-ITM LEAPS, tested with my own honest costs (independent of Codex).
